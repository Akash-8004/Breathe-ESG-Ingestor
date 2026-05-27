# MODEL.md — Data Model Documentation

## Overview

The Breathe ESG Ingestor uses a **two-layer data architecture** designed to preserve raw source data integrity while enabling normalization and review workflows. This document explains the rationale behind each model and how they interact.

---

## Why Two Layers: RawRecord + EmissionEntry

### RawRecord — The Immutable Source of Truth

Every row from every uploaded file is stored as a `RawRecord` with the original payload preserved in a `JSONB` field. RawRecords are:

- **Immutable**: Once created, the `raw_payload` is never modified
- **Append-only**: Records are only ever inserted, never updated or deleted
- **Source-agnostic**: The `raw_payload` stores whatever the source provided, regardless of format

This design serves three critical purposes:

1. **Audit trail**: An auditor can always trace a normalized emission entry back to the exact data that was submitted
2. **Re-processing**: If normalization logic changes (e.g., updated emission factors), we can re-process raw records without requiring a new file upload
3. **Error forensics**: When a `PARSE_ERROR` occurs, the raw payload is preserved for debugging — the analyst can see exactly what data caused the failure

### EmissionEntry — The Normalized Working Record

`EmissionEntry` is the computed, normalized record derived from a `RawRecord`. It contains:

- The original quantity and unit (what came in)
- The normalized quantity in `kgCO2e` (what we computed)
- The emission factor and its source (how we computed it)
- A review status that can change through the approval workflow

EmissionEntries are **mutable only pre-approval**. The status can transition through:
```
PENDING → APPROVED (terminal — no further changes after approval)
PENDING → FLAGGED → APPROVED or REJECTED
PENDING → REJECTED
```

### One-to-One Relationship

Each `RawRecord` produces at most one `EmissionEntry`. If parsing fails (bad data, unknown material, etc.), the `RawRecord` is created with `parse_status=PARSE_ERROR` and no `EmissionEntry` is generated. This means:

- `RawRecord` count = total rows in the file
- `EmissionEntry` count = successfully parsed rows
- `error_count` = `RawRecord` count - `EmissionEntry` count

---

## Multi-Tenancy Enforcement

Multi-tenancy is enforced through the **Tenant** model and **user-based resolution**:

### Data Model

```
Tenant
  ├── User (FK: tenant)
  ├── DataSource (FK: tenant)
  ├── EmissionEntry (FK: tenant)
  └── (IngestionRun accessed via DataSource.tenant)
```

### How It Works

1. Every `User` has a `tenant` FK set at account creation
2. Every API view resolves the tenant from `request.user.tenant`
3. Every queryset is filtered by `tenant=request.user.tenant`
4. There is **no tenant in the URL or header** — this prevents data leakage through URL manipulation

### Example (from `EmissionEntryListView`):

```python
def get_queryset(self):
    return EmissionEntry.objects.filter(tenant=self.request.user.tenant)
```

This pattern is consistent across all views. Even `IngestionRun` queries go through the data source's tenant:

```python
IngestionRun.objects.filter(data_source__tenant=tenant)
```

---

## Scope Assignment Logic

Scope (1, 2, or 3) is assigned **at parse time** based on the source type and material/category:

| Source Type | Scope   | Rationale |
|-------------|---------|-----------|
| SAP (fuel)  | Scope 1 | Direct emissions from fuel combustion at owned/controlled facilities |
| Utility     | Scope 2 | Indirect emissions from purchased electricity |
| Travel      | Scope 3 | Other indirect emissions from business travel (not owned/controlled) |

This aligns with the GHG Protocol Corporate Standard:
- **Scope 1**: Direct GHG emissions from sources owned or controlled by the company
- **Scope 2**: Indirect GHG emissions from purchased energy
- **Scope 3**: All other indirect emissions in the value chain

The scope is embedded in the parser logic — the SAP parser always sets `SCOPE_1`, utility always sets `SCOPE_2`, and travel always sets `SCOPE_3`. There is no dynamic scope resolution because in this system's domain, the source type deterministically maps to scope.

---

## Unit Normalization Chain

Every data source provides quantities in different units. The normalization chain converts everything to **kgCO2e** (kilograms of CO2 equivalent):

### SAP (Fuel)

```
Original unit (GAL, M3, L, KG)
  → Convert to base unit (L or M3)
    GAL → L (×3.78541)
    M3 stays as M3 for natural gas
    L, KG pass through
  → Multiply by emission factor
    DIESEL: 2.68 kgCO2e/L
    PETROL: 2.31 kgCO2e/L
    LPG: 1.51 kgCO2e/L
    NAT_GAS: 2.04 kgCO2e/m3
  → Result: quantity_normalized in kgCO2e
```

### Utility (Electricity)

```
Original unit (kWh or MWh)
  → Convert to kWh
    MWh → kWh (×1000)
  → Multiply by emission factor
    India grid: 0.82 kgCO2e/kWh (CEA 2022)
  → Result: quantity_normalized in kgCO2e
```

### Travel

```
Flights:
  Distance in km (from data or Haversine)
  → Multiply by emission factor per cabin class
    Economy: 0.255 kgCO2e/km
    Business: 0.573 kgCO2e/km
  → Apply short-haul uplift if <1000km (×1.15)
  → Result: quantity_normalized in kgCO2e

Hotels:
  Room-nights × 20.6 kgCO2e/room-night

Ground transport:
  Distance in km × factor
    Taxi/Car: 0.21 kgCO2e/km
    Train: 0.041 kgCO2e/km
```

### Storage

Both the original and normalized values are stored:
- `quantity` + `unit` — what came in (e.g., 150 GAL)
- `quantity_normalized` + `unit_normalized` — what we computed (e.g., 1522.33 kgCO2e)
- `emission_factor` + `emission_factor_source` — how we computed it

This allows auditors to verify the calculation chain at any time.

---

## Audit Trail Design

The `AuditTrail` model records every status change on an `EmissionEntry`:

### Design Principles

1. **Append-only**: Records are only ever created, never updated or deleted
2. **Automatic**: Written by the system on every status change (CREATED, FLAGGED, APPROVED, REJECTED)
3. **Actor-tracked**: Every action records which user performed it
4. **Timestamped**: Immutable timestamp set at creation
5. **Notes**: Optional context for why the action was taken (e.g., flag reason)

### Lifecycle

```
1. File uploaded → parser creates EmissionEntry
   → AuditTrail: CREATED by [uploading user]

2. Analyst flags an entry with reason
   → AuditTrail: FLAGGED by [analyst], notes = reason

3. Analyst approves the entry
   → AuditTrail: APPROVED by [analyst]
```

### Why No Soft-Deletes

Once an entry is APPROVED, it becomes part of the auditable emissions record. There are no soft-deletes because:
- Deleting approved entries would break audit integrity
- The correct workflow is REJECT (not delete) for entries that shouldn't count
- Rejected entries remain in the system with their full audit trail
