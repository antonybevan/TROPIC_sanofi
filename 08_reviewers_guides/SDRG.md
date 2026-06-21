# Study Data Reviewer's Guide (SDRG)

**Study Name:** TROPIC Re-Analysis  
**Compound:** Cabazitaxel (CbzP) vs. Mitoxantrone (MP)  
**Standard (submission):** CDISC SDTMIG v3.4 + CDISC/NCI CT 2026-03-27 (uplifted; see §5)  
**Standard (source):** CDISC SDTMIG v3.1.1 (PDS 2013 release; pristine `01_raw_source/real_sdtm/`)  
**Created:** 2026-05-23 · **Uplifted:** 2026-06-20  

---

## 1. Source Data Normalization & Integrity Controls
Source data are the official **Sanofi de-identified SDTM datasets** for NCT00417079, released in 2013 and accessed via the **Project Data Sphere (PDS)** repository. The files are SAS transport datasets (`*.sas7bdat`); no other source format is used (this matches `README.md` *Data provenance* and `REPRODUCIBILITY.md` §5).

The custom SAS staging compiler ([L_staging_ingest.sas](file:///Users/apple/Desktop/TROPIC/02_production_sas/L_staging_ingest.sas)) ingests these SDTM `*.sas7bdat` files (`set realsdtm.<domain>`) and performs automated supplemental-qualifier (SUPP--) transposition and merge, coercing character-encoded continuous indicators (e.g. age, laboratory values, vital measurements) into standardized double-precision numeric values.

> [!IMPORTANT]
> **Single-Arm Source Limitation:** The source Project Data Sphere (PDS) public dataset contains only the Mitoxantrone (MP) arm (N=371). The comparator Cabazitaxel (CbzP) arm (N=378) was not included in the public release. Consequently, the SDTM datasets only represent the MP cohort. In our pipeline, the core production (SAS) and validation (R) ADaM tracks process strictly the MP cohort (N=371) to establish a clean double-programming validation setup. The comparator Cabazitaxel cohort is reconstructed from published trial literature and merged dynamically at the final reporting/TFL compilation step in [tfl_generation.R](file:///Users/apple/Desktop/TROPIC/09_tfl/tfl_generation.R).

### Database Write-Protection Architecture
To guarantee database integrity and prevent raw data corruption during pipeline executions:
- The `realsdtm` SAS libref (pointing to `01_raw_source/real_sdtm/`) is mounted with `access=readonly` in [00_config.sas](file:///Users/apple/Desktop/TROPIC/02_production_sas/00_config.sas), preventing direct writes via that libref.
- The `staging` SAS libref (same physical directory) is writable, allowing `L_staging_ingest.sas` to write transposed SUPP-merged domain outputs alongside source files during ODA cloud execution.
- Intermediate mapped SDTM outputs generated during mapping runs are redirected to [sdtm_mapped](file:///Users/apple/Desktop/TROPIC/04_adam/sdtm_mapped/) inside the [04_adam](file:///Users/apple/Desktop/TROPIC/04_adam/) output folder.


---

## 2. SDTM Domain Mapping Summary
Standard SDTM mapping structures were built in `S_sdtm_mapping.sas` under the trial-era **SDTM-IG 3.1.1** standard (per SAP v3.0 §1; the source data predates later IG versions):
* **DM (Demographics):** Unique subject identifier `USUBJID` constructed via `STUDYID || '-' || SITEID || '-' || SUBJID`. Randomization date `RANDDT` and treatment start date `TRTSDT` mapped to standard ISO 8601 date fields.
* **EX (Exposure):** Normalised cycle-level actual administered doses (`EXDOSE` in mg).
* **AE (Adverse Events):** Coded utilizing MedDRA dictionaries into `AEDECOD`, `AEBODSYS`, and standard CTCAE toxicity grades. **Date Precision Note:** The source PDS dataset contains AE timing as week-offset integers (`AESTWK`, `AEENWK`). AE start/end dates are reconstructed as `RFSTDTC + (AESTWK - 1) * 7` and `RFSTDTC + (AEENWK - 1) * 7`. This reconstruction yields calendar-week accuracy (±3.5 days) rather than exact calendar dates. This precision level was present in the source data and is not a programming artefact. All safety analyses using AE dates (ADAE, ADTTE TTSAE) inherit this limitation.
* **LB (Laboratory):** Mapped continuous Absolute Neutrophil Count (ANC) and Prostate Specific Antigen (PSA) measurements.
* **DS (Disposition):** Captured study completion reasons, trial exits, and survival follow-up records.
* **RS (Response / Efficacy Fallback):** Derived from `DS` domain where `DSDECOD` indicates progression or death. Death records are mapped to standard RS structures with `RSSTRESC = 'DEATH'` to capture survival outcomes cleanly as efficacy checkpoints.

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

This imputation strategy has no formal SAP section (the SAP v3.0 specifies no missing-data imputation method); it is a documented design choice per ADRG §5.1. **These imputed baseline laboratory constants are schema placeholders and are NOT used as covariates or stratification factors in any efficacy model**, consistent with [ADRG](file:///Users/apple/Desktop/TROPIC/08_reviewers_guides/ADRG.md) §5.1. The primary and secondary Cox / log-rank analyses stratify **only** on `ECOGBL` and `MEASDISF` (see `09_tfl/tfl_generation.R`, `compute_tte_stats()` → `strata(ECOGBL, MEASDISF)`). `ALBBL` and `LDHBL` in particular are single constants for all subjects (no subject-level source available) and therefore carry no subject-level information; they are retained purely to satisfy the ADaM schema and should be read as "not available," not as analysis inputs.

### 4.2 Supplemental Domain Ingestion
Domains `LS` (Lesion) and `PN` (Pain/Numeric) do not have supplemental (`SUPPLS`, `SUPPPN`) datasets in the PDS source data. The `%transpose_supp()` macro gracefully handles this via the `supp_exists = 0` guard path, copying the primary domain directly without SUPP merge.

### 4.3 Country and Region Assignment
The DM domain in the source data does not contain country-of-study-site information. `COUNTRY` is assigned `'IND'` and `REGION` as `'REST OF WORLD'` for all subjects. Geographic subgroup analyses were not pre-specified in SAP v3.0 and are not reported.

### 4.4 Hardcoded Demographic Constant (SEX = 'M')
The demographics domain (`DM`) contains a hardcoded variable `SEX = 'M'` assigned to all subjects in `A_adsl_generation.sas`. This is a clinical decision consistent with the trial protocol for metastatic castration-resistant prostate cancer (mCRPC), which is an exclusively male patient population. To ensure metadata conformity, the Define-XML codelist references are maintained; however, no female subjects are present in the analysis dataset.

---

## 5. SDTMIG 3.4 Conformance Uplift (2026-06-20)

The pristine source SDTM (`01_raw_source/real_sdtm/`, PDS 2013) was authored to **SDTMIG 3.1.1**, which is below the FDA Data Standards Catalog support floor. A derived, conformance-uplifted SDTM layer was produced to **SDTMIG 3.4 + CDISC/NCI CT 2026-03-27** and is the version described by `define_sdtm.xml` and packaged in `m5/.../tabulations/sdtm/`. The raw source is **never modified**; the uplift is a deterministic derivation step (`06_telemetry/uplift_sdtm_34.R` for data, `07_define_xml/uplift_define_34.py` for the define).

**Standard derivations applied (each preserves source data values):**
- **DM.AGE** derived numeric from the de-identified `AGEGRP` (the PDS release masked exact age into `AGEGRP`; subjects coded `>=85` are floored to `AGE=85`, with the cap flagged in `SUPPDM` `QNAM=AGEGRP`). The non-standard `AGEGRP` is removed from DM. `ACTARM`/`ACTARMCD` added (single completed arm, code `A`).
- **AE.AESOC** populated equal to `AEBODSYS` (MedDRA SOC already carried in `AEBODSYS`).
- **EPOCH** derived for AE/EX/VS (DS already carried it). Subject Elements (SE) are absent from the de-identified extract, so EPOCH is derived from the collected `VISIT` structure: `SCREENING`→SCREENING; `BASELINE`/`CYCLE n`/`END OF TREATMENT`→TREATMENT; `FOLLOW-UP n`→FOLLOW-UP; `UNSCHEDULED`→TREATMENT. All values are valid EPOCH CT.
- **EX.EXENDY** derived (study day of `EXENDTC` vs `RFSTDTC`).
- **Week-offset timing** (`AESTWK`/`AEENWK`/`AESTWKF`/`AEENWKF`, `DSSTWK`/`DSSTWKF`) — non-standard in the parent domains — relocated to **`SUPPAE`/`SUPPDS`** as supplemental qualifiers (linked by `IDVAR`/`IDVARVAL`), preserving the ±3.5-day timing (see §2 Date Precision Note and the date-precision sensitivity analysis, `06_telemetry/DATE_PRECISION_SENSITIVITY_2026-06-20.md`).
- Redundant **`SUBJID`** removed from non-DM domains; non-standard `ARM2`/`ARMA`/`ARMCD2` (define-only phantoms, never in data) dropped from `IG.DM`.
- **TS** enriched with public NCT00417079 parameters (`NARMS=2`, `ACTSUB=371`, `SSTDTC=2007`, `AGEMIN=P18Y`). **TA** (Trial Arms) built from the public two-arm design.
- Variable labels title-cased, leading/trailing whitespace stripped, variable order aligned to the CDISC SDTM library.

**Authoritative conformance run.** Validated with **CDISC CORE** (`cdisc-rules-engine`) at `-s sdtmig -v 3.4` (CT 2026-03-27) — report `06_telemetry/conformance/core_sdtm34_report.json`, run record `CORE_SDTM34_RUN_RECORD.md`. All targeted structural rules cleared (CORE-000264 AESOC, -000453 AGE, -000701 EPOCH, -000776 EXENDY, -000550 non-standard→SUPP, -000852 variable order, -001082 type, -000594/398 labels, -000867 whitespace). Remaining findings are **not programming defects** and fall into four documented classes:
1. **Inherent to de-identification (5):** expected/required variables removed by the PDS public release (`SITEID`, `COUNTRY`, MedDRA hierarchy codes `AELLT`/`AEPTCD`, exact `AESTDTC`/`AEENDTC`). Cannot be reconstructed.
2. **Real source-data quality (CORE-000266/022 AESER consistency; CORE-000732 VSSTRESC/N):** present in the source safety data; **not** silently overwritten (doing so would falsify reported safety data).
3. **Cross-domain (CORE-000767 RELREC/`FAOBJ`):** fires because no `FA` domain is in this analysis-scoped package; not applicable to the submitted domains.
4. **CORE engine-internal** ("evaluation dataset failed to build").
