# Breathe ESG Ingestor

A production-ready Django REST + React application that ingests emissions/activity data from three real-world enterprise sources, normalizes all data into a unified emissions ledger, and surfaces a review dashboard for analysts to inspect, flag, and approve rows before audit lock.

## 🔑 Demo Credentials

| Field    | Value                |
| -------- | -------------------- |
| Username | `analyst@acme.com` |
| Password | `password123`      |

## 🏗️ Tech Stack

- **Backend**: Django 4.2 + Django REST Framework
- **Frontend**: React 18 + Vite, Axios, Recharts
- **Database**: PostgreSQL (SQLite fallback for local dev)
- **Auth**: DRF Token Authentication
- **Deployment**: Railway (backend) + Netlify/Vercel (frontend)

## 📁 Project Structure

```
BreateESG/
├── backend/              # Django REST API
│   ├── breathe_esg/      # Project settings
│   ├── users/            # Tenant + User models, auth endpoints
│   ├── ingestion/        # DataSource, IngestionRun, RawRecord, parsers
│   ├── emissions/        # EmissionEntry, AuditTrail, dashboard
│   └── core/             # Emission factors, IATA data, Haversine, seed command
├── frontend/             # React 18 + Vite SPA
│   └── src/
│       ├── pages/        # Login, Dashboard, Ingest, RunDetail, Review
│       ├── components/   # Reusable UI components
│       └── styles/       # CSS design system
├── sample_data/          # Three sample CSV files
├── MODEL.md              # Data model documentation
├── DECISIONS.md          # Design decisions
├── TRADEOFFS.md          # What was deliberately not built
└── SOURCES.md            # Real-world data source research
```

## 🚀 Running Locally

### Prerequisites

- **Python 3.8–3.12** (`python --version`)
- **Node.js 18+** and npm (`node -v`, `npm -v`)
- **Git** (for version control and deployment)
- PostgreSQL is **not** required for local dev — the app uses SQLite by default

### Backend

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment variables (already pre-configured for local dev)
cp .env.example .env      # On Windows: copy .env.example .env

# Run migrations
python manage.py migrate

# Seed demo data (creates tenant, user, and ingests all sample files)
python manage.py seed_data

# Start server
python manage.py runserver
```

The API will be available at `http://localhost:8000/api/`.

### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Copy environment variables
cp .env.example .env      # On Windows: copy .env.example .env

# Start dev server
npm run dev
```

The frontend will be available at `http://localhost:5173/`.

### Environment Variables (Local Dev)

**Backend** (`backend/.env`):

| Variable                 | Local Value                                     |
| ------------------------ | ----------------------------------------------- |
| `SECRET_KEY`           | Dev key (change in production)                  |
| `DEBUG`                | `True`                                        |
| `DATABASE_URL`         | `sqlite:///db.sqlite3`                        |
| `CORS_ALLOWED_ORIGINS` | `http://localhost:5173,http://localhost:3000` |

**Frontend** (`frontend/.env`):

| Variable         | Local Value                   |
| ---------------- | ----------------------------- |
| `VITE_API_URL` | `http://localhost:8000/api` |

## 📡 API Endpoints

| Method | Endpoint                                  | Description                              |
| ------ | ----------------------------------------- | ---------------------------------------- |
| POST   | `/api/auth/login/`                      | Login, returns auth token                |
| POST   | `/api/auth/logout/`                     | Logout, deletes token                    |
| GET    | `/api/ingestion-runs/`                  | List all runs for tenant                 |
| POST   | `/api/ingestion-runs/`                  | Upload file + source_type                |
| GET    | `/api/ingestion-runs/{id}/`             | Run detail                               |
| GET    | `/api/ingestion-runs/{id}/raw-records/` | Paginated raw records                    |
| GET    | `/api/emission-entries/`                | All emission entries (no pagination)     |
| GET    | `/api/emission-entries/{id}/`           | Entry detail + raw payload + audit trail |
| POST   | `/api/emission-entries/{id}/approve/`   | Approve an entry                         |
| POST   | `/api/emission-entries/{id}/flag/`      | Flag with reason                         |
| POST   | `/api/emission-entries/{id}/reject/`    | Reject an entry                          |
| GET    | `/api/dashboard/summary/`               | Dashboard aggregation                    |
| GET    | `/api/data-sources/`                    | List data sources                        |

### Filter Parameters for `/api/emission-entries/`

- `?status=PENDING|FLAGGED|APPROVED|REJECTED`
- `?source_type=SAP|UTILITY|TRAVEL`
- `?scope=SCOPE_1|SCOPE_2|SCOPE_3`
- `?date_from=YYYY-MM-DD&date_to=YYYY-MM-DD`
- `?run_id={ingestion_run_id}`

### Dashboard Summary Response Fields

```json
{
  "total_entries": 154,
  "pending_count": 140,
  "approved_count": 10,
  "flagged_count": 2,
  "rejected_count": 2,
  "scope_1_total": "12345.67",
  "scope_2_total": "8901.23",
  "scope_3_total": "4567.89",
  "sap_count": 45,
  "utility_count": 24,
  "travel_count": 40
}
```

## 🗂️ Sample Data Reference

The `sample_data/` folder contains three CSV files that the app is designed to parse. **The app expects data in these exact formats** — uploading CSVs with different column names, delimiters, or structures will result in parse errors.

### 1. SAP Fuel Export → Scope 1 (`sample_data/sap_export.csv`)

**Format**: Semicolon-delimited (`;`), SAP MB51/ME2M flat-file export style

| Column | SAP Field | Description | Example |
|--------|-----------|-------------|---------|
| `MANDT` | Client | SAP client ID | `100` |
| `WERKS` | Plant | Facility/plant code | `IN01`, `US_WEST` |
| `MATNR` | Material No. | Fuel material code | `DIESEL`, `PETROL`, `LPG`, `NAT_GAS` |
| `MAKTX` | Material Desc. | Human-readable description | `Diesel Fuel HSD` |
| `MENGE` | Quantity | Amount consumed | `500.00` |
| `MEINS` | Unit | Unit of measure | `L` (liters), `GAL` (gallons), `M3` (cubic meters) |
| `DMBTR` | Amount | Cost in local currency | `42500.00` |
| `WAERS` | Currency | Currency code | `INR`, `USD` |
| `BUDAT` | Posting Date | Date of activity | `20240115` or `15.01.2024` |

**Sample rows:**
```
MANDT;WERKS;MATNR;MAKTX;MENGE;MEINS;DMBTR;WAERS;BUDAT
100;IN01;DIESEL;Diesel Fuel HSD;500.00;L;42500.00;INR;20240115
100;US_WEST;DIESEL;Diesel Fuel ULSD;150.00;GAL;675.00;USD;20240120
100;IN01;NAT_GAS;Natural Gas Pipeline;800.00;M3;48000.00;INR;20240125
```

**Accepted material codes**: `DIESEL`, `PETROL`, `LPG`, `NAT_GAS` (others → parse error)

**Built-in edge cases** (rows 47–51 in the sample file):
| Row | Issue | Parser Result |
|-----|-------|---------------|
| 47 | Empty quantity field | `PARSE_ERROR: Missing quantity` |
| 48 | `LUBRICANT` — no emission factor | `PARSE_ERROR: Unrecognized material` |
| 49 | `-50 GAL` — negative quantity | `PARSE_ERROR: Non-positive quantity` |
| 50 | `XYZMAT` — unknown material | `PARSE_ERROR: Unrecognized material` |
| 51 | Date `20291231` — future date | `PARSE_ERROR: Future date not allowed` |

---

### 2. Utility Electricity Export → Scope 2 (`sample_data/utility_export.csv`)

**Format**: Comma-delimited (`,`), electricity utility portal export style

| Column | Description | Example |
|--------|-------------|---------|
| `AccountNumber` | Utility account ID | `ACC-001` |
| `MeterID` | Meter identifier | `MTR-A101` |
| `ServiceAddress` | Facility address | `Unit 4 Block B Whitefield Bangalore` |
| `BillingPeriodStart` | Billing period start | `2023-01-17` |
| `BillingPeriodEnd` | Billing period end | `2023-02-14` |
| `ReadingDate` | Meter reading date | `2023-02-14` |
| `MeterReading` | Current meter reading | `45230` |
| `Units` | Unit of measure | `kWh` or `MWh` |
| `PreviousReading` | Previous meter reading | `44010` |
| `Consumption` | Energy consumed | `1220` |
| `TariffCode` | Billing tariff | `LT-2A`, `HT-1` |
| `BilledAmount` | Invoice amount | `9760.00` |
| `Currency` | Currency code | `INR` |

**Sample rows:**
```
AccountNumber,MeterID,ServiceAddress,BillingPeriodStart,BillingPeriodEnd,ReadingDate,MeterReading,Units,PreviousReading,Consumption,TariffCode,BilledAmount,Currency
ACC-001,MTR-A101,Unit 4 Block B Whitefield Bangalore 560066,2023-01-17,2023-02-14,2023-02-14,45230,kWh,44010,1220,LT-2A,9760.00,INR
ACC-002,MTR-B205,Plot 12 MIDC Pune Industrial Area 411057,2023-01-20,2023-02-18,2023-02-18,128500,MWh,125.200,3.3,HT-1,264000.00,INR
```

**Built-in edge cases** (rows 24–25 in the sample file):
| Row | Issue | Parser Result |
|-----|-------|---------------|
| 24 | Duplicate billing period (overlapping dates) | `PARSE_ERROR: Overlapping billing period` |
| 25 | Empty consumption field | `PARSE_ERROR: Missing consumption` |

---

### 3. Corporate Travel Export → Scope 3 (`sample_data/travel_export.csv`)

**Format**: Comma-delimited (`,`), Concur/Navan expense report export style

| Column | Description | Example |
|--------|-------------|---------|
| `ReportID` | Expense report ID | `RPT-001` |
| `EmployeeID` | Employee identifier | `EMP-101` |
| `EmployeeName` | Full name | `Anika Sharma` |
| `CostCenter` | Department cost center | `CC-ENG` |
| `TripPurpose` | Reason for travel | `Client Meeting` |
| `ExpenseType` | Type of expense | `Flight`, `Hotel`, `Ground Transport` |
| `TravelDate` | Date of travel | `2024-01-15` |
| `Origin` / `Destination` | City names | `Mumbai`, `Delhi` |
| `OriginCode` / `DestCode` | IATA airport codes | `BOM`, `DEL` |
| `CabinClass` | Flight class | `Economy`, `Business` |
| `DistanceKM` | Flight distance (optional — calculated via Haversine if missing) | `1148` |
| `HotelName` / `HotelCity` | Hotel details | `Taj Palace`, `Delhi` |
| `HotelNights` | Number of room-nights | `2` |
| `GroundTransportMode` | Ground transport type | `Taxi`, `Rental Car`, `Train` |
| `AmountUSD` | Expense amount | `450.00` |
| `LocalCurrency` | Local currency code | `INR`, `USD`, `GBP` |

**Sample rows:**
```
ReportID,EmployeeID,EmployeeName,CostCenter,TripPurpose,ExpenseType,TravelDate,Origin,Destination,OriginCode,DestCode,CabinClass,DistanceKM,HotelName,HotelCity,HotelNights,GroundTransportMode,AmountUSD,LocalCurrency
RPT-001,EMP-101,Anika Sharma,CC-ENG,Client Meeting,Flight,2024-01-15,Mumbai,Delhi,BOM,DEL,Economy,1148,,,,,450.00,INR
RPT-001,EMP-101,Anika Sharma,CC-ENG,Client Meeting,Hotel,2024-01-15,,,,,,,Taj Palace,Delhi,2,,180.00,USD
RPT-001,EMP-101,Anika Sharma,CC-ENG,Client Meeting,Ground Transport,2024-01-15,Delhi,,,,,,,,50,Taxi,35.00,INR
```

**Built-in edge cases:**
| Row | Issue | Parser Result |
|-----|-------|---------------|
| 9 | Missing DistanceKM for BOM→LHR flight | Auto-calculated via Haversine: 7,196 km |
| 36 | Ground transport with no distance | Uses default 50 km |
| 37 | Missing DestCode (LHR → blank) | Falls back to city name lookup |

---

### ⚠️ Important: Custom Data Format Limitations

The app's parsers are built specifically for the column names and formats shown above. **If you upload a CSV with different column names or a different structure, the parser will fail.** For example:

- A SAP file using commas instead of semicolons → won't parse
- A utility file with `Energy_Used` instead of `Consumption` → won't parse
- A travel file without IATA airport codes → distance calculation may fail

This is by design — in real-world ESG platforms, each data source integration is custom-built for that source's specific export format.

Since the source-to-scope mapping is always 1:1, the Review page uses a single **Scope** filter (no separate Source filter).

## 🔍 Review Workflow

The Review page is the core analyst workflow. For each emission entry, the analyst can:

| Action              | When to Use                                                                |
| ------------------- | -------------------------------------------------------------------------- |
| ✅**Approve** | Data looks correct — quantity, factor, and calculation verified           |
| 🚩**Flag**    | Something suspicious — prompts for a reason (e.g., "Quantity 3× normal") |
| ❌**Reject**  | Data is clearly wrong — duplicate, test data, or invalid values           |

### Entry Detail (Expand View)

Clicking the ▸ arrow on any entry fetches the full detail from the API, showing:

- **Entry Details**: Original quantity, emission factor, factor source, facility, cost, calculation breakdown
- **Calculation Breakdown**: `830 M3 × 2.04 kgCO2e/M3 = 1,693.2 kgCO2e`
- **Raw Payload**: The exact original CSV row preserved as JSON
- **Audit Trail**: Full history of who created/approved/flagged/rejected the entry

### Available Filters

- **Status**: Pending, Approved, Flagged, Rejected
- **Scope**: Scope 1, Scope 2, Scope 3
- **Date Range**: From / To date pickers

## 📖 Documentation

- [MODEL.md](MODEL.md) — Data model rationale and design
- [DECISIONS.md](DECISIONS.md) — All design decisions with reasoning
- [TRADEOFFS.md](TRADEOFFS.md) — What was deliberately not built
- [SOURCES.md](SOURCES.md) — Real-world data source research

## ⚙️ Emission Factors

| Source              | Factor | Unit              | Reference  |
| ------------------- | ------ | ----------------- | ---------- |
| Diesel              | 2.68   | kgCO2e/L          | DEFRA 2023 |
| Petrol              | 2.31   | kgCO2e/L          | DEFRA 2023 |
| LPG                 | 1.51   | kgCO2e/L          | DEFRA 2023 |
| Natural Gas         | 2.04   | kgCO2e/m³        | DEFRA 2023 |
| Electricity (India) | 0.82   | kgCO2e/kWh        | CEA 2022   |
| Flight (Economy)    | 0.255  | kgCO2e/km         | DEFRA 2023 |
| Flight (Business)   | 0.573  | kgCO2e/km         | DEFRA 2023 |
| Hotel               | 20.6   | kgCO2e/room-night | HCMI       |
| Taxi/Car            | 0.21   | kgCO2e/km         | DEFRA 2023 |
| Train               | 0.041  | kgCO2e/km         | DEFRA 2023 |
