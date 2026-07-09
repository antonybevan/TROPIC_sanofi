# Study Data Reviewer's Guide (SDRG)

| Field | Value |
|---|---|
| **Document** | Study Data Reviewer's Guide (SDRG) |
| **Study** | TROPIC / EFC6193 / NCT00417079 |
| **Compound** | Cabazitaxel (CbzP) vs Mitoxantrone (MP) |
| **Standard (package layer)** | CDISC SDTMIG **v3.4** + CDISC/NCI CT 2026-03-27 (uplifted; §5) |
| **Standard (pristine source)** | CDISC SDTMIG **v3.1.1** (PDS 2013; local `01_source_data/real_sdtm/`) |
| **Document version** | 1.1 (Path A hardened) |
| **Effective** | 2026-07-09 |
| **Supersedes** | SDRG narrative drafts prior to `v0.1.0-demo-rc.1` Path A freeze |
| **Product claim** | **Path A only** — controlled non-submission demonstration |

---

## 0. What this package is / is not (read first)

| This package **is** | This package **is not** |
|---|---|
| Study-data explanation for a **submission-style** Module 5 tree | An FDA filing / real application sequence |
| Real **MP-only** de-identified SDTM (N=371) as source for dual-language ADaM | Two-arm real patient-level IPD in git |
| Uplifted SDTMIG 3.4 **package layer** + define co-located under `m5/.../tabulations/sdtm/` | Proof that commercial P21 cleared every residual |
| CORE SDTM 3.4 run with **classified residuals** (F-015) | “Full CORE clean” / zero-finding claim |
| Week-offset / partial-date source honesty (F-017) | Day-level AE timing precision that the source never had |
| Path A demo with patient XPT **not redistributed** | Part 11 validated system |

**Binding claim:** [`docs/PRODUCT_CLAIM.md`](../../docs/PRODUCT_CLAIM.md)  
**Source intake pack (WS-1):** [`docs/workstreams/WS1_SOURCE_INTAKE_PACK.md`](../../docs/workstreams/WS1_SOURCE_INTAKE_PACK.md)  
**Residual risks:** [`docs/workstreams/WS5_KNOWN_DIFFERENCES_MEMO.md`](../../docs/workstreams/WS5_KNOWN_DIFFERENCES_MEMO.md)  
**External validation slots:** [`docs/workstreams/WS3_EXTERNAL_VALIDATION_EVIDENCE_INDEX.md`](../../docs/workstreams/WS3_EXTERNAL_VALIDATION_EVIDENCE_INDEX.md)  
**Sealed demo RC:** tag `v0.1.0-demo-rc.1` · [`docs/RELEASE_NOTE_v0.1.0-demo-rc.1.md`](../../docs/RELEASE_NOTE_v0.1.0-demo-rc.1.md) · `python3 scripts/verify_release.py`  
**Review package face:** [`08_submission_package/m5/datasets/tropic/tabulations/sdtm/`](../../08_submission_package/m5/datasets/tropic/tabulations/sdtm/)  
**Analysis narrative:** [`ADRG.md`](ADRG.md)  
**Findings disposition:** `06_qc_evidence/audit/FINDINGS_DISPOSITION_BOARD.md`

> **Redistribution:** Real `*.sas7bdat` and package `*.xpt` are **not** in git (data rights + portfolio surface policy). Structure, define, SDRG/ADRG, and programs are.

---

## 1. Source data normalization & integrity controls

Source data are the official **Sanofi de-identified SDTM** for NCT00417079 (2013), accessed via **Project Data Sphere (PDS)** as SAS `*.sas7bdat`. Provenance: root README · [`00_governance/REPRODUCIBILITY.md`](../../00_governance/REPRODUCIBILITY.md).

Staging: [`L_staging_ingest.sas`](../../04_analysis_datasets/programs/sas/L_staging_ingest.sas) (and R twin `v_staging_ingest.R`) ingests `realsdtm.<domain>`, transpose-merges SUPP--, and coerces character continuous indicators to numeric where required.

> [!IMPORTANT]
> **Single-arm source limitation (Path A critical):** PDS public data here is **MP only (N=371)**. Cabazitaxel is **not** present as source SDTM. Dual-language ADaM recon is MP-only. Synthetic/reconstructed CbzP is merged only at TFL reporting ([`tfl_generation.R`](../../05_outputs/tfl/tfl_generation.R)) — non-confirmatory (F-003). Do not describe this as a clean two-arm double-programming of trial IPD.

### Database write-protection architecture

- `realsdtm` libref → `01_source_data/real_sdtm/` with `access=readonly` in [`00_config.sas`](../../04_analysis_datasets/programs/sas/00_config.sas)
- `staging` libref writable for SUPP-merged intermediates during ODA runs
- Mapped intermediates redirect under `04_analysis_datasets/adam/` (local build outputs; not the git portfolio face)


---

## 2. SDTM Domain Mapping Summary
Standard SDTM mapping structures were built in `S_sdtm_mapping.sas` from trial-era **SDTM-IG 3.1.1** source data; SAP v4.0 treats this as source provenance and requires the release package to use the governed SDTMIG 3.4 uplift layer:
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

This imputation strategy is retained as a documented implementation limitation under SAP v4.0 §14 / §18. **These imputed baseline laboratory constants are schema placeholders and are NOT used as covariates or stratification factors in any efficacy model**, consistent with [ADRG](ADRG.md) §5.1. The primary and secondary Cox / log-rank analyses stratify **only on the protocol randomization strata** (`ECOGBL` and `MEASDISF`; see `05_outputs/tfl/tfl_generation.R`, `compute_tte_stats()` → `strata(ECOGBL, MEASDISF)`). `ALBBL` and `LDHBL` in particular are single constants for all subjects (no subject-level source available) and therefore carry no subject-level information; they are retained purely to satisfy the ADaM schema and should be read as "not available," not as analysis inputs.

### 4.2 Supplemental Domain Ingestion
Domains `LS` (Lesion) and `PN` (Pain/Numeric) do not have supplemental (`SUPPLS`, `SUPPPN`) datasets in the PDS source data. The `%transpose_supp()` macro gracefully handles this via the `supp_exists = 0` guard path, copying the primary domain directly without SUPP merge.

### 4.3 Country and Region Assignment
The DM domain in the source data does not contain country-of-study-site information. `COUNTRY` is assigned `'IND'` and `REGION` as `'REST OF WORLD'` for all subjects. Geographic subgroup analyses are not part of SAP v4.0 reporting and are not reported.

### 4.4 Hardcoded Demographic Constant (SEX = 'M')
The demographics domain (`DM`) contains a hardcoded variable `SEX = 'M'` assigned to all subjects in `A_adsl_generation.sas`. This is a clinical decision consistent with the trial protocol for metastatic castration-resistant prostate cancer (mCRPC), which is an exclusively male patient population. To ensure metadata conformity, the Define-XML codelist references are maintained; however, no female subjects are present in the analysis dataset.

### 4.5 Partial/Imprecise Source Date Values (CM, LB, LS, PN)
The independent R SDTM validation (`04_analysis_datasets/programs/r/v_sdtm_validation.log`) raises four `[WARNING]`s flagging partial or imprecise ISO-8601 date values in source date fields: `CMSTDTC` (CM), `LBDTC` (LB), `LSDTC` (LS), and `PNDTC` (PN) — e.g. `----07`, `--12-26`, `2009---04`. These are **expected manifestations of the source PDS public-release date precision** (the same root cause documented in §2 and §5.1), not programming defects: the values are carried through as-is rather than fabricating spurious precision. They surface as WARNINGs (not ERRORs); no analysis depends on day-level precision in these fields. No action required.

---

## 5. SDTMIG 3.4 Conformance Uplift (2026-06-20)

The pristine source SDTM (`01_source_data/real_sdtm/`, PDS 2013) was authored to **SDTMIG 3.1.1**, which is below the FDA Data Standards Catalog support floor. A derived, conformance-uplifted SDTM layer was produced to **SDTMIG 3.4 + CDISC/NCI CT 2026-03-27** and is the version described by `define_sdtm.xml` and packaged in `08_submission_package/m5/.../tabulations/sdtm/`. The raw source is **never modified**; the uplift is a deterministic derivation step (`platform/uplift_sdtm_34.R` for data, `03_metadata/define/uplift_define_34.py` for the define).

**Standard derivations applied (each preserves source data values):**
- **DM.AGE** derived numeric from the de-identified `AGEGRP` (the PDS release masked exact age into `AGEGRP`; subjects coded `>=85` are floored to `AGE=85`, with the cap flagged in `SUPPDM` `QNAM=AGEGRP`). The non-standard `AGEGRP` is removed from DM. `ACTARM`/`ACTARMCD` added (single completed arm, code `A`).
- **AE.AESOC** populated equal to `AEBODSYS` (MedDRA SOC already carried in `AEBODSYS`).
- **EPOCH** derived for AE/EX/VS (DS already carried it). Subject Elements (SE) are absent from the de-identified extract, so EPOCH is derived from the collected `VISIT` structure: `SCREENING`→SCREENING; `BASELINE`/`CYCLE n`/`END OF TREATMENT`→TREATMENT; `FOLLOW-UP n`→FOLLOW-UP; `UNSCHEDULED`→TREATMENT. All values are valid EPOCH CT.
- **EX.EXENDY** derived (study day of `EXENDTC` vs `RFSTDTC`).
- **Week-offset timing** (`AESTWK`/`AEENWK`/`AESTWKF`/`AEENWKF`, `DSSTWK`/`DSSTWKF`) — non-standard in the parent domains — relocated to **`SUPPAE`/`SUPPDS`** as supplemental qualifiers (linked by `IDVAR`/`IDVARVAL`), preserving the ±3.5-day timing (see §2 Date Precision Note and the date-precision sensitivity analysis, `06_qc_evidence/audit/run_records/DATE_PRECISION_SENSITIVITY_2026-06-20.md`).
- Redundant **`SUBJID`** removed from non-DM domains; non-standard `ARM2`/`ARMA`/`ARMCD2` (define-only phantoms, never in data) dropped from `IG.DM`.
- **TS** enriched with public NCT00417079 parameters (`NARMS=2`, `ACTSUB=371`, `SSTDTC=2007`, `AGEMIN=P18Y`). **TA** (Trial Arms) built from the public two-arm design.
- Variable labels title-cased, leading/trailing whitespace stripped, variable order aligned to the CDISC SDTM library.

### 5.1 CORE SDTMIG 3.4 — honesty (F-015)

**Run record:** [`platform/conformance/CORE_SDTM34_RUN_RECORD.md`](../../platform/conformance/CORE_SDTM34_RUN_RECORD.md)  
**Engine:** cdisc-rules-engine (CORE) v0.16.0 · standard SDTMIG 3.4 · CT 2026-03-27  
**Headline:** targeted **structural uplift rules cleared**; overall issue count is **not zero** and must not be marketed as “CORE clean.”

| Class | Examples | Disposition (Path A) |
|---|---|---|
| **Structural targets fixed** | AESOC, AGE, EPOCH, EXENDY, non-standard→SUPP, labels/order/type | Accept as uplift success |
| **Inherent de-identification** | SITEID / COUNTRY / MedDRA hierarchy codes / exact AE dates removed by PDS | **Accept** — cannot invent PII or lost codes |
| **Real source-data quality** | AESER consistency (CORE-000266/022); VSSTRESC/N (CORE-000732) | **Accept** — do not overwrite true safety source to greenwash |
| **Cross-domain N/A** | RELREC/FAOBJ (CORE-000767) without FA in analysis-scoped package | **Waive / N/A** for this package scope |
| **Engine-internal** | CORE-000929 / CORE-001081 evaluation dataset failed to build | **Accept with note** — tool noise, not silent data fix |

**Rule for reviewers:**  
- **Do claim:** “Uplifted package layer; CORE run recorded; structural targets cleared; residuals classified.”  
- **Do not claim:** “Full commercial conformance” or “zero CORE findings.”  
- **Open engineering (WS-1):** rule-level CSV matrix still planned (`docs/workstreams/WS1_CORE_RESIDUAL_MATRIX.csv` — not yet filed). Until then, this section + run record + known-differences memo are the residual story.

**Related residual:** week-offset / partial ISO dates — **F-017** (§2 AE note, §4.5). Never invent day precision.

**Pinnacle 21 commercial ADaM/SDTM:** **NOT_AVAILABLE** under Path A (see WS-3 external validation index). Local CORE + dual-language ADaM recon are substitutes only.
