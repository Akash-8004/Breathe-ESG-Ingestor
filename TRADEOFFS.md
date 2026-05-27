# TRADEOFFS.md — What Was Deliberately Not Built

This document describes three significant capabilities that were intentionally excluded from the Breathe ESG Ingestor prototype. Each exclusion was a deliberate scope decision to ensure the features we did build are complete, defensible, and production-quality.

---

## 1. Dynamic Emission Factor Database

### What we built instead
Hardcoded DEFRA 2023, CEA 2022, and HCMI emission factors in `core/emission_factors.py`. Every factor is centralized with its source citation.

### What a production system would need
A versioned emission factor library with:
- **Temporal versioning**: DEFRA publishes updated factors annually. A production system would apply the correct year's factors to data from that year (e.g., 2022 factors for 2022 data, 2023 factors for 2023 data).
- **Gas-by-gas breakdown**: Our system uses a single kgCO2e factor. Production systems need CO2, CH4, and N2O separately because some reporting frameworks (CDP, TCFD) require gas-specific disclosures.
- **Geographic specificity**: Our electricity factor uses India grid average (0.82 kgCO2e/kWh). A production system needs state-level or grid-region factors (e.g., Karnataka vs. Tamil Nadu have different grid mixes).
- **Factor source management**: Supporting multiple factor databases (DEFRA, EPA, IPCC, ecoinvent) with audit trail for which was applied and why.
- **Factor update workflow**: When new factors are published, ability to recalculate historical entries with updated values and track the delta.

### Why we skipped it
Building a proper emission factor database is a 4–6 week effort that involves:
1. Data modeling for factor versions, applicability rules, and geographic scoping
2. Importing and validating factor datasets (DEFRA alone has ~300 line items)
3. Building a factor selection engine that picks the right factor based on activity type, date, and location
4. Testing factor calculations against reference implementations

The hardcoded approach is correct enough for a prototype — the values match published sources, and every EmissionEntry records which factor was used.

---

## 2. PDF Utility Bill Parsing

### What we built instead
CSV file upload from utility portal exports. Users download their usage data as CSV from the utility's web portal and upload it to our system.

### What a production system would need
Many smaller utility accounts (especially in India) only provide bills as PDFs. A production system would need:
- **OCR engine**: Tesseract (open source) or a cloud service (Google Vision, AWS Textract) to extract text from scanned PDFs.
- **Per-utility templates**: BESCOM, MSEDCL, Tata Power, BSES Delhi each have completely different PDF layouts. Each requires a custom extraction template that maps visual regions to data fields.
- **Template versioning**: Utilities update their bill formats 1–2 times per year. Templates need to be updated accordingly, with fallback logic for unrecognized layouts.
- **Validation pipeline**: OCR is error-prone. Extracted values need validation (is this a reasonable consumption number? Does the billing period make sense? Does the total match units × rate?).
- **Manual review fallback**: When OCR confidence is low, route to a human reviewer.

### Why we skipped it
1. **Cost**: Cloud OCR APIs charge per page. At scale, this becomes a significant recurring cost.
2. **Accuracy**: OCR on scanned Indian utility bills (often photographed, not scanned) has ~85–90% accuracy. The remaining 10–15% requires manual review, which partially defeats the automation.
3. **Maintenance**: Per-utility templates are fragile. A utility redesign breaks the template and requires engineering effort to fix.
4. **Coverage**: Portal CSV covers the majority of medium-to-large accounts, which are our primary target market.

### Acknowledged gap
Clients with PDF-only utility bills would need to manually enter data or use a third-party OCR service. This should be addressed in v2 with a phased approach: start with the 5 most common Indian utilities.

---

## 3. Statistical Anomaly Detection

### What we built instead
Rule-based issue detection:
- Missing data → `PARSE_ERROR` with descriptive message
- Unknown materials/units → `PARSE_ERROR`
- Overlapping billing periods → `FLAGGED` with explanation
- Estimated distances → `FLAGGED` with reason
- Future dates → `PARSE_ERROR`
- Non-positive quantities → `PARSE_ERROR`

### What a production system would need
Statistical anomaly detection that flags entries based on historical patterns:
- **Time-series outlier detection**: "This month's electricity consumption is 4× the 6-month moving average" — likely a data error or a real event worth investigating.
- **Cross-facility benchmarking**: "Plant IN02 consumed 3× more diesel per unit of output than Plant IN01" — potential data quality issue or operational concern.
- **Year-over-year comparison**: "Scope 1 emissions increased 25% compared to same quarter last year" — should be investigated before reporting.
- **Seasonal pattern detection**: "Winter heating fuel consumption is expected to be higher — this entry is within normal seasonal range."
- **Machine learning models**: After accumulating enough historical data, train models to detect patterns that rule-based systems miss.

### Why we skipped it
1. **Data volume**: Anomaly detection needs historical data to establish baselines. A new deployment has no history — the models would generate too many false positives initially.
2. **Domain complexity**: "Normal" emissions vary dramatically by industry, facility size, geography, and season. A model trained on one client's data wouldn't apply to another.
3. **Scope discipline**: The prompt explicitly states "build less, but build it well." Adding anomaly detection would mean building ML infrastructure (data pipeline, model training, threshold management, false-positive review workflow) on top of the core ingestion system.
4. **Incremental value**: The rule-based checks catch the most common data quality issues (missing data, format errors, duplicates). Statistical anomalies are a v2 feature that becomes valuable after 6–12 months of data accumulation.
