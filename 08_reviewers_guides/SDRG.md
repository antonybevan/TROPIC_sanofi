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
* **AE (Adverse Events):** Coded utilizing MedDRA dictionaries into `AEDECOD`, `AEBODSYS`, and standard CTCAE toxicity grades.
* **LB (Laboratory):** Mapped continuous Absolute Neutrophil Count (ANC) and Prostate Specific Antigen (PSA) measurements.
* **DS (Disposition):** Captured study completion reasons, trial exits, and survival follow-up records.

---

## 3. Reference Ranges & Baseline Criteria
* Baseline lab and vitals measurements are defined as the last non-missing assessment completed prior to first exposure (`ADY <= 0`).
* Normal reference ranges (`LBNRLO` and `LBNRHI`) were preserved from raw PDS metadata. Lab values outside these ranges are flagged accordingly in `LBNRIND`.
