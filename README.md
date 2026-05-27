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

## 🗂️ Data Sources & Scope Mapping

| Source            | Format                                               | Scope             | Emission Calculation                      |
| ----------------- | ---------------------------------------------------- | ----------------- | ----------------------------------------- |
| **SAP**     | Semicolon-delimited CSV (MB51/ME2M fuel exports)     | **Scope 1** | Fuel quantity × DEFRA 2023 factor        |
| **Utility** | Portal CSV (electricity consumption in kWh/MWh)      | **Scope 2** | Electricity × CEA 2022 India grid factor |
| **Travel**  | Concur/Navan CSV (flights, hotels, ground transport) | **Scope 3** | Distance × DEFRA 2023 factor per mode    |

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
