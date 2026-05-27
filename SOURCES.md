# SOURCES.md — Real-World Data Source Research

For each of the three data sources integrated into the Breathe ESG Ingestor, this document describes:
1. What real-world format was researched and what was found
2. What the sample data looks like and why it's shaped that way
3. What would break in a real deployment (honest assessment)

---

## Source 1: SAP — Fuel & Procurement Data

### What We Researched

SAP provides several mechanisms for extracting data:

| Method | Description | Feasibility |
|--------|-------------|-------------|
| **Flat-file export** | CSV/TSV from transactions MB51 (goods movement history) or ME2M (purchase order list) | ✅ Universally available, no IT setup |
| **IDoc** | Intermediate Document for EDI-based B2B exchange | ❌ Designed for system-to-system EDI, not reporting |
| **OData/CDS** | RESTful API via SAP Gateway/Fiori | ⚠️ Requires Gateway setup most ECC clients lack |
| **BAPI/RFC** | Direct function call to SAP system | ⚠️ Requires RFC connector + SAP authorizations |
| **SAP BW/BEx** | Business Warehouse reporting | ⚠️ Requires BW license and configured InfoProviders |

**Finding**: In 80%+ of real sustainability projects, the data path is: sustainability team → plant manager → run MB51 → filter by material group → export to Excel/CSV → email to sustainability team. This is the format we support.

### Sample Data Shape

Our `sap_export.csv` contains 50 rows with:

- **Semicolon delimiter**: SAP's default export delimiter (not comma), reflecting actual SAP system output configuration
- **German-influenced column headers**: `MANDT` (Mandant/Client), `WERKS` (Plant), `MATNR` (Material Number), etc. — these are the actual SAP technical field names
- **Mixed date formats**: `YYYYMMDD` (SAP internal) and `DD.MM.YYYY` (SAP display format). Which format appears depends on the user's SAP GUI settings and export method. Both are common in practice.
- **Multiple plants**: `IN01`, `IN02` (India plants), `US_WEST` (US facility). Plant codes in SAP are arbitrary 4-character identifiers — they have no inherent meaning without a plant master lookup.
- **Mixed units**: L (liters), GAL (US gallons), M3 (cubic meters), KG (kilograms). Different plants may use different unit systems.
- **5 bad rows**: Null quantity, LUBRICANT (no emission factor), negative quantity, unknown material code, future date. These reflect real data quality issues we've seen in SAP exports.

### What Would Break in a Real Deployment

1. **Character encoding**: SAP exports from German/Chinese systems may use ISO-8859-1 or Windows-1252 encoding instead of UTF-8. Our parser uses `utf-8-sig` which handles BOM but not alternate encodings.
2. **Material master mapping**: In real SAP systems, material numbers are arbitrary codes (e.g., `000000001234567`), not human-readable names like `DIESEL`. We'd need a material-to-fuel-type mapping table maintained per client.
3. **Multiple currency amounts**: SAP stores amounts in both document currency and local currency. The `DMBTR` field is local currency. For multi-country operations, we'd need exchange rate handling.
4. **SAP transports between systems**: Different SAP systems (development, QA, production) may have different material masters. An export from the wrong system would have invalid material numbers.
5. **Large file sizes**: A year of goods movements for a manufacturing company can easily be 100,000+ rows. Our synchronous parser would timeout — we'd need background task processing (Celery).

---

## Source 2: Utility Data — Electricity

### What We Researched

Utility data is available through several channels:

| Method | Description | Feasibility |
|--------|-------------|-------------|
| **Portal CSV export** | Download from utility's customer portal | ✅ Available from most utilities |
| **PDF bills** | Monthly utility bill PDFs | ⚠️ Requires OCR + per-utility template |
| **Green Button** | US standard for utility data exchange | ⚠️ US-only, limited utility adoption |
| **UtilityAPI** | Third-party API aggregator | ⚠️ Requires client enrollment, US-focused |
| **Manual entry** | Manually key in from bills | ❌ Error-prone, doesn't scale |

**Finding**: Indian utilities (BESCOM, MSEDCL, Tata Power, BSES) and major US utilities (Con Edison, PG&E, Duke Energy) all offer CSV or Excel download of usage history from their customer portals. The format varies by utility but follows a recognizable pattern: account, meter, dates, readings, consumption.

### Sample Data Shape

Our `utility_export.csv` contains 24 rows with:

- **Two meters**: `MTR-A101` (small commercial, kWh) and `MTR-B205` (industrial, MWh). This reflects a real scenario where a company has multiple utility accounts at different facilities.
- **Non-calendar billing periods**: Billing periods like Jan 17 – Feb 14 (not Jan 1 – Jan 31). Real utility billing follows the meter reading schedule, not calendar months.
- **Mixed units**: kWh for small accounts, MWh for large industrial accounts. Utilities report in MWh when consumption is in the thousands of kWh range.
- **Overlapping billing periods** (row 23): MTR-B205 has a duplicate period for Jun 19 – Jul 19 with a different consumption value. This represents a bill correction — the utility re-issued the bill after an actual meter reading replaced an estimated one.
- **Null consumption** (row 24): MTR-A101 has meter readings (59900 and 58220) but no pre-computed Consumption value. This happens when the utility exports raw readings without the computed delta. Our parser computes it: 59900 – 58220 = 1680 kWh.

### What Would Break in a Real Deployment

1. **Date format inconsistency**: US utilities use MM/DD/YYYY, Indian utilities use DD/MM/YYYY, and ISO dates (YYYY-MM-DD) appear in API exports. Our parser handles several formats but may miss edge cases.
2. **Meter multiplier**: Some industrial meters have a CT (Current Transformer) ratio that multiplies the raw reading. If the utility exports raw readings without applying the multiplier, our consumption calculation would be wrong by 100×–200×.
3. **Estimated readings**: Utilities sometimes estimate readings when they can't access the meter. These are later corrected, creating the overlapping billing periods we flag. But if we don't receive the corrected bill, the estimated reading persists.
4. **Multiple service types**: A single utility account may have electricity, gas, and water. Our parser assumes electricity — a real deployment would need to filter by service type.
5. **Grid emission factor variation**: We use a single India grid average (0.82 kgCO2e/kWh). In reality, India's grid factor varies by region (Southern grid ≈ 0.82, Northern grid ≈ 0.93) and by time of day (renewable-heavy during daytime). Location-specific factors would significantly improve accuracy.

---

## Source 3: Corporate Travel — Flights, Hotels, Ground Transport

### What We Researched

Corporate travel data is available through:

| Method | Description | Feasibility |
|--------|-------------|-------------|
| **CSV export from TMC** | Export from Concur, Navan, TripActions | ✅ Available to travel managers |
| **Concur API v4** | REST API with OAuth 2.0 | ⚠️ Requires app registration (1–3 week approval) |
| **Navan webhooks** | Real-time event notifications | ⚠️ Requires Enterprise subscription + public endpoint |
| **Credit card data** | Parse corporate card transactions | ⚠️ No distance/route info, only amounts |
| **Manual entry** | Employees self-report | ❌ Low compliance, inaccurate |

**Finding**: Concur and Navan both provide "Travel Report Export" in their admin consoles. The CSV format includes trip details (dates, routes, cabin class), hotel stays, and ground transport — all the data needed for Scope 3 business travel calculations. A travel manager can export this covering any date range in under 2 minutes.

### Sample Data Shape

Our `travel_export.csv` contains 40 rows across three expense types:

**Flights (20 rows)**:
- Routes using 8 IATA airports: BOM, DEL, LHR, JFK, DXB, SIN, SFO, CDG
- Some rows have `DistanceKM` pre-populated (direct from the booking system), others have only `OriginCode` + `DestCode` (requiring Haversine calculation)
- Mix of Economy and Business class (different emission factors: 0.255 vs 0.573 kgCO2e/km)
- Short-haul flights (DEL-BOM ≈ 1148km, LHR-CDG ≈ 340km) get the ×1.15 short-haul uplift
- **3 rows with missing DestCode** (rows 36–38): Carlos Ruiz's itinerary has incomplete airport codes → these produce `PARSE_ERROR`

**Hotels (10 rows)**:
- Real hotel names and cities matching the flight destinations
- 1–5 nights per stay
- Multiple currencies (INR, USD, GBP, EUR, SGD, AED)

**Ground Transport (10 rows)**:
- Taxi, Rental Car, and Train
- Some have `DistanceKM`, others don't (Taxi in Delhi, Dubai — no distance means estimated 50km → FLAGGED)
- Train between Paris locations (120km, 0.041 kgCO2e/km)

### What Would Break in a Real Deployment

1. **IATA code coverage**: We only have 8 airports in our lookup. A real system would need all ~9,000 IATA-coded airports. A flight BOM→BLR (Bangalore) would fail with "Unknown airport code: BLR" even though it's a major Indian route.
2. **Multi-leg flights**: Our parser treats each row as a direct flight. Real itineraries often have connections (e.g., BOM→DXB→LHR). The booking system may report each leg separately or combine them — we'd need to handle both cases.
3. **Cabin class normalization**: Concur uses "Economy", "Premium Economy", "Business", "First". Navan uses "Y", "W", "J", "F". We'd need a mapping table for each TMC's class codes.
4. **Hotel emission factors**: Our 20.6 kgCO2e/room-night is a global average. In reality, hotel emissions vary enormously: a budget hotel in India ≈ 8 kgCO2e/room-night, a luxury hotel in Dubai ≈ 45 kgCO2e/room-night. Country-specific and star-rating-specific factors would improve accuracy.
5. **Radiative forcing**: Our flight emission factors include a basic uplift for short-haul but don't fully account for radiative forcing (the non-CO2 climate effects of high-altitude emissions like contrails, NOx, and water vapor). DEFRA recommends a ×1.9 multiplier for this, which we don't apply separately.
6. **Employee data privacy**: Travel reports contain employee names, cost centers, and trip purposes. In a production deployment, we'd need to handle GDPR/privacy requirements — potentially anonymizing employee data or getting consent for data processing.
