# Breathe ESG — Frontend

React 18 + Vite SPA for the Breathe ESG Ingestor.

## Setup

```bash
npm install
cp .env.example .env    # On Windows: copy .env.example .env
npm run dev             # Starts at http://localhost:5173
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| `VITE_API_URL` | Backend API URL (default: `http://localhost:8000/api`) |

## Pages

| Route | Page | Description |
|-------|------|-------------|
| `/login` | Login | Token-based authentication |
| `/dashboard` | Dashboard | Summary cards, scope chart, source breakdown, recent runs |
| `/ingest` | Ingest Data | Upload SAP, Utility, or Travel CSV files |
| `/runs/:id` | Run Detail | Ingestion run metadata, success/error row counts |
| `/review` | Review Entries | Filter, inspect, approve/flag/reject emission entries |

## Key Components

| Component | Purpose |
|-----------|---------|
| `SummaryCards` | Dashboard stat cards (total, pending, approved, flagged) |
| `ScopeChart` | Bar chart showing emissions by Scope 1/2/3 (Recharts) |
| `SourceBreakdown` | Horizontal bar breakdown by data source |
| `EmissionTable` | Sortable table with expand-to-detail, approve/flag/reject actions |
| `EntryDetail` | Expanded view: entry fields, calculation breakdown, raw payload, audit trail |
| `FileUploadTab` | Drag-and-drop file upload with source type mapping |
| `RecentRuns` | Clickable list of recent ingestion runs |

## Build for Production

```bash
npm run build           # Output in dist/
npm run preview         # Preview production build locally
```

## Deployment

Pre-configured for Netlify (`netlify.toml`) and Vercel (`vercel.json`) with SPA routing fallbacks.
Set `VITE_API_URL` to the production backend URL in the hosting dashboard.
