# DECISIONS.md — Design Decisions

Every ambiguity in this project was resolved with a deliberate decision. This document records each one in the format: **"I chose X over Y because Z. If I could ask the PM, I'd ask: ..."**

---

## 1. SAP Data Format: Flat-File Export over IDoc / OData / BAPI

**I chose** semicolon-delimited CSV flat-file exports (from SAP transactions MB51 or ME2M) **over** IDoc, OData, or BAPI integration.

**Because:**
- **IDocs** are EDI-specific (B2B document exchange). They require an EDI partner profile and are designed for system-to-system communication (e.g., purchase orders between companies), not for extracting internal procurement data for sustainability reporting.
- **OData** requires SAP Fiori/Gateway setup, which many organizations — especially those running older ECC systems — don't have configured. It also requires an OData service to be published for the specific data entities needed.
- **BAPIs** require a direct RFC (Remote Function Call) connection to the SAP system, which means setting up a middleware connector (e.g., PyRFC), firewall rules, and a service account with appropriate SAP authorizations. This is weeks of IT coordination.
- **Flat-file CSV** is what a sustainability lead or plant manager actually receives. They run MB51 (goods movement history) or ME2M (purchase order list), filter by material group, and export. This takes 2 minutes and requires zero IT involvement.

**If I could ask the PM, I'd ask:** "Do any of our target clients have SAP Gateway/Fiori configured and would prefer an OData integration? Should we plan for this in v2?"

---

## 2. Utility Data Format: Portal CSV over PDF / API

**I chose** utility portal CSV exports **over** PDF bill parsing or utility API integration.

**Because:**
- **PDF bills** would require OCR (Tesseract, Google Vision, or a paid API like Textract) and per-utility template matching. Indian utilities (BESCOM, MSEDCL, Tata Power) each have completely different PDF layouts, and these layouts change without notice. Building reliable PDF extraction is a 2–4 week effort per utility, and it breaks when the utility updates their bill template.
- **Utility APIs** (Green Button, UtilityAPI) require the client to enroll their utility account with the API provider. This is a multi-week process involving utility approval, and many Indian utilities don't support it at all.
- **Portal CSV** covers 80%+ of real cases. Every major utility portal (BESCOM, Tata Power, Con Edison, PG&E) has a "Download Usage Data" or "Export Bills" function that produces a CSV. The sustainability team can export this in minutes.

**If I could ask the PM, I'd ask:** "What percentage of our clients have PDF-only utility bills? Should we prioritize OCR integration or recommend clients contact their utility for CSV access?"

---

## 3. Travel Data Format: CSV Export over Concur API / Navan Webhook

**I chose** CSV exports from Concur or Navan **over** direct API or webhook integration.

**Because:**
- **Concur API (v4)** requires OAuth 2.0 app registration, which needs SAP Concur admin approval. The process takes 1–3 weeks and requires a production-grade OAuth flow with token refresh. The API also has rate limits and pagination complexity.
- **Navan webhooks** require a publicly accessible endpoint, webhook signature verification, and handling of event-driven data (which doesn't match our batch-oriented ingestion model). Also requires a Navan Enterprise subscription.
- **CSV export** is available in both platforms under "Reports" → "Travel Report" → "Export". A travel manager can download a CSV covering any date range in 2 minutes. The format is standardized enough that a single parser handles both Concur and Navan exports.

**If I could ask the PM, I'd ask:** "Are any clients interested in real-time travel tracking (webhook-based)? Or is batch processing (monthly/quarterly) sufficient for their reporting cadence?"

---

## 4. SAP Material Subset: Fuel Materials Only

**I chose** to handle only fuel materials (DIESEL, PETROL, LPG, NAT_GAS) from SAP exports, **not** all procurement data.

**Because:**
- SAP MM handles procurement for everything: office supplies, raw materials, packaging, chemicals, fuel, etc. Only fuel materials have a direct, well-understood emission factor (fuel combustion = Scope 1 direct emissions).
- Other materials (e.g., steel, cement, chemicals) require a supply-chain emission factor database (Scope 3, Category 1: Purchased Goods), which is a fundamentally different and much more complex calculation. Building this properly would require an emissions factor database with thousands of material-specific factors.
- By limiting to fuel, we ensure every emission calculation is defensible and auditable.

**If I could ask the PM, I'd ask:** "Should we plan to support Scope 3 Category 1 (purchased goods) from SAP? If so, which emission factor database should we integrate (DEFRA, ecoinvent, EXIOBASE)?"

---

## 5. Missing Flight Distance: Haversine Fallback, Then Error

**I chose** to use Haversine great-circle distance as a fallback when `DistanceKM` is missing in travel data, and `PARSE_ERROR` when airport codes are also missing.

**Because:**
- Many travel exports include origin/destination IATA codes but not distance. Haversine gives a distance accurate to within ~0.5% (assuming spherical Earth).
- DEFRA 2023 recommends using Great Circle Distance for flight emission calculations, so Haversine aligns with standard methodology.
- If both distance and airport codes are missing, there is no defensible way to estimate emissions, so `PARSE_ERROR` is the correct response.
- We embed a small IATA coordinate lookup for the 8 airports specified in scope (BOM, DEL, LHR, JFK, DXB, SIN, SFO, CDG). Unknown airport codes also produce a `PARSE_ERROR`.

**If I could ask the PM, I'd ask:** "Should we integrate a full IATA airport database (~9,000 airports) for production use, or is the curated list sufficient for our initial client base?"

---

## 6. Overlapping Utility Billing Periods: Flagged, Not Rejected

**I chose** to flag overlapping billing periods (status = FLAGGED) **rather than** rejecting them outright.

**Because:**
- Overlapping billing periods in utility data usually represent **bill corrections** — the utility re-issued a bill for a period that was already billed. This is common when estimated readings are later corrected with actual readings.
- Rejecting them would lose the correction data. Flagging them preserves the data and puts the decision in the analyst's hands. The analyst can:
  - Approve the corrected bill and reject the original
  - Approve both if they represent different consumption components
  - Reject the correction if it's a duplicate error
- The `flagged_reason` field contains a clear explanation: "Overlapping billing period detected for meter MTR-xxx: this period overlaps with existing period..."

**If I could ask the PM, I'd ask:** "Should we implement automatic resolution of bill corrections (e.g., always prefer the later bill for the same period)? Or is manual analyst review always required?"

---

## 7. Emission Factors: Hardcoded over Dynamic Factor Database

**I chose** to hardcode emission factors from DEFRA 2023, CEA 2022, and HCMI **rather than** building a dynamic emission factor database.

**Because:**
- A proper emission factor database is a significant modeling effort. It needs: versioned factors by year, gas-by-gas breakdown (CO2, CH4, N2O), geographic specificity (country/region), source citations, and a factor selection engine.
- DEFRA publishes updated factors annually. For a prototype, hardcoded 2023 values are correct enough and fully auditable — every `EmissionEntry` records which factor was used and its source.
- The factors are centralized in `core/emission_factors.py`, making them easy to update in one place.

**If I could ask the PM, I'd ask:** "Should we plan for multi-year factor support (e.g., apply 2022 factors to 2022 data, 2023 factors to 2023 data)? How often do clients need to recalculate with updated factors?"

---

## 8. Multi-Tenancy Resolution: User's Tenant FK, Not URL or Header

**I chose** to resolve the tenant from the authenticated user's `tenant` FK **rather than** from a URL path parameter (e.g., `/api/tenants/{id}/...`) or a custom HTTP header (e.g., `X-Tenant-ID`).

**Because:**
- **URL-based tenancy** is vulnerable to enumeration attacks — a user could try different tenant IDs in the URL to access other tenants' data.
- **Header-based tenancy** has the same risk and adds complexity to the frontend (which header to set, when, with what value).
- **User-based tenancy** is inherently secure — the tenant is determined by who you are, not by what you request. A user can only ever see their own tenant's data because every queryset filters by `request.user.tenant`.
- This also simplifies the API surface — no tenant parameter needed in any endpoint.

**If I could ask the PM, I'd ask:** "Will any users need to switch between tenants (e.g., a consultant managing multiple clients)? If so, we'd need a tenant-switching mechanism."

---

## 9. Single Scope Filter over Separate Source + Scope Filters

**I chose** to use a single **Scope** filter on the Review page **rather than** having both a Source filter and a Scope filter.

**Because:**
- In this system, the source-to-scope mapping is **always 1:1**: SAP → Scope 1, Utility → Scope 2, Travel → Scope 3. There is no scenario where a source produces multiple scopes.
- Having both filters is redundant — selecting "SAP" in the Source filter is identical to selecting "Scope 1" in the Scope filter.
- From an ESG analyst's perspective, **Scope** is the more meaningful categorization. Analysts think in terms of "Scope 1 direct emissions" vs "Scope 2 purchased energy" — not in terms of which enterprise system the data came from.
- Removing the redundant filter simplifies the UI and reduces cognitive load.

**If I could ask the PM, I'd ask:** "If we add new source types in the future (e.g., fleet telematics for Scope 1, or renewable energy certificates for Scope 2), should we re-introduce the Source filter since multiple sources could then map to the same scope?"

---

## 10. No Pagination on Emission Entries over Global Page Size

**I chose** to disable DRF pagination (`pagination_class = None`) on the `/api/emission-entries/` endpoint **rather than** using the global `PAGE_SIZE = 50`.

**Because:**
- The global DRF pagination silently truncated results — the dashboard showed 154 entries but the Review page only displayed 50 with no indication that more existed.
- For a prototype with hundreds of entries, returning all results in a single response is acceptable and simpler than building frontend pagination controls (page numbers, next/previous buttons, total count display).
- The frontend filter system (status, scope, date range) already reduces the working set significantly.
- Adding server-side pagination with frontend controls would be a v2 feature when clients have thousands of entries per tenant.

**If I could ask the PM, I'd ask:** "What's the expected data volume per tenant? If clients ingest thousands of entries per month, we should implement cursor-based pagination with frontend page controls."

---

## 11. On-Demand Detail Fetch over Eager Loading

**I chose** to fetch the full entry detail (raw payload + audit trail) **on demand when the analyst expands a row** rather than including it in the list response.

**Because:**
- The list endpoint returns lightweight data (date, scope, category, quantity, status) for all entries. Including `raw_payload` (which can be large JSON objects) and `audit_trail` (which grows over time) for every entry would significantly increase response size.
- Most entries in the list will never be expanded — an analyst typically only expands entries they want to inspect more closely.
- The detail is cached client-side after the first fetch, so re-expanding the same row is instant.
- This follows the standard **list/detail pattern** in REST API design — list endpoints are lightweight, detail endpoints are comprehensive.

**If I could ask the PM, I'd ask:** "Should we add a bulk-approve feature for entries that pass all validation? This would reduce the need to expand individual entries and speed up the analyst workflow."
