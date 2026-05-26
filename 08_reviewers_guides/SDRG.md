# Study Data Reviewer's Guide (SDRG)

**Study Name:** TROPIC Re-Analysis  
**Compound:** Cabazitaxel (CbzP) vs. Mitoxantrone (MP)  
**Standard:** CDISC SDTM IG v3.4  
**Created:** 2026-05-23  

---

## 1. Source Data Normalization
Source data was ingested from the de-identified **Project Data Sphere (PDS)** data repository for NCT00417079. 

Raw JSON records were loaded via the custom SAS staging compiler (`L_staging_ingest.sas`), which coerced character-encoded continuous indicators (e.g. age, laboratory values, vital measurements) into standardized double-precision numerical values.

---

## 2. SDTM Domain Mapping Summary
Standard SDTM mapping structures were built in `S_sdtm_mapping.sas` under SDTM-IG 3.4 guidelines:
* **DM (Demographics):** Unique subject identifier `USUBJID` constructed via `STUDYID || '-' || SITEID || '-' || SUBJID`. Randomization date `RANDDT` and treatment start date `TRTSDT` mapped to standard ISO 8601 date fields.
* **EX (Exposure):** Normalised cycle-level actual administered doses (`EXDOSE` in mg).
* **AE (Adverse Events):** Coded utilizing MedDRA dictionaries into `AEDECOD`, `AEBODSYS`, and standard CTCAE toxicity grades. **Date Precision Note:** The source PDS dataset contains AE timing as week-offset integers (`AESTWK`, `AEENWK`). AE start/end dates are reconstructed as `RFSTDTC + (AESTWK × 7)` and `RFSTDTC + (AEENWK × 7)`. This reconstruction yields calendar-week accuracy (±3.5 days) rather than exact calendar dates. This precision level was present in the source data and is not a programming artefact. All safety analyses using AE dates (ADAE, ADTTE TTOS) inherit this limitation.
* **LB (Laboratory):** Mapped continuous Absolute Neutrophil Count (ANC) and Prostate Specific Antigen (PSA) measurements.
* **DS (Disposition):** Captured study completion reasons, trial exits, and survival follow-up records.

---

## 3. Reference Ranges & Baseline Criteria
* Baseline lab and vitals measurements are defined as the last non-missing assessment completed prior to first exposure (`ADY <= 0`).
* Normal reference ranges (`LBNRLO` and `LBNRHI`) were preserved from raw PDS metadata. Lab values outside these ranges are flagged accordingly in `LBNRIND`.

---

## 4. Known Data Limitations & Derivation Decisions

### 4.1 Baseline Laboratory Imputation
For subjects with missing baseline laboratory values (PSABL, ALPBL, HGBBL), population-median proxy values have been imputed in ADSL:
- `PSABL` default: 110.0 ng/mL
- `ALPBL` default: 140.0 U/L  
- `HGBBL` default: 11.5 g/dL
- `ALBBL` fixed: 38.0 g/L (no subject-level source available)
- `LDHBL` fixed: 220.0 U/L (no subject-level source available)

This imputation strategy is specified in SAP v3.0 §4.3. These imputed values are used **only** for baseline covariate stratification in subgroup Cox models. Primary endpoint analyses (OS, PFS) do not use these baseline lab variables as time-varying inputs.

### 4.2 Supplemental Domain Ingestion
Domains `LS` (Lesion) and `PN` (Pain/Numeric) do not have supplemental (`SUPPLS`, `SUPPPN`) datasets in the PDS source data. The `%transpose_supp()` macro gracefully handles this via the `supp_exists = 0` guard path, copying the primary domain directly without SUPP merge.

### 4.3 Country and Region Assignment
The DM domain in the source data does not contain country-of-study-site information. `COUNTRY` is assigned `'IND'` and `REGION` as `'REST OF WORLD'` for all subjects. Geographic subgroup analyses were not pre-specified in SAP v3.0 and are not reported.
