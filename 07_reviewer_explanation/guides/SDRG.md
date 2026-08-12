# Study Data Reviewer's Guide (SDRG)

| Field | Value |
|---|---|
| **Document** | Study Data Reviewer's Guide (SDRG) |
| **Study** | TROPIC / EFC6193 / NCT00417079 |
| **Compound** | Cabazitaxel (CbzP) vs Mitoxantrone (MP) |
| **Standard (package layer)** | CDISC SDTMIG **v3.4** + CDISC/NCI CT 2026-03-27 (uplifted; §5) |
| **Standard (pristine source)** | CDISC SDTMIG **v3.1.1** (PDS 2013; local `01_source_data/real_sdtm/`) |
| **Document version** | 1.3 (audit closure / portfolio release) |
| **Effective** | 2026-08-05 |
| **Supersedes** | SDRG v1.2 from the `v0.2.0-portfolio` release (which superseded the `v0.1.0-demo-rc.1` baseline) |
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
**Current portfolio release:** tag `v0.2.2-portfolio` · [`docs/RELEASE_NOTE_v0.2.2-portfolio.md`](../../docs/RELEASE_NOTE_v0.2.2-portfolio.md) · `python3 scripts/verify_release.py`
**Review package face:** [`08_submission_package/m5/datasets/tropic/tabulations/sdtm/`](../../08_submission_package/m5/datasets/tropic/tabulations/sdtm/)
**Analysis narrative:** [`ADRG.md`](ADRG.md)
**Findings disposition:** `06_qc_evidence/audit/FINDINGS_DISPOSITION_BOARD.md`

> **Redistribution:** Real `*.sas7bdat` and package `*.xpt` are **not** in git (data rights + portfolio surface policy). Structure, define, SDRG/ADRG, and programs are.

---

## 0A. CRF grounding (principal source-fidelity rule)

**CRF PDF (source):** `01_source_data/Sanofi CRF Tropic.pdf` (EFC6193, FINAL 21-Nov-2006)
**In package:** `blankcrf.pdf` under tabulations/sdtm (source CRF copy — **not** claimed as a complete annotated aCRF with page-level define origins)
**Decision record:** [`docs/workstreams/reviews/WS1_CRF_GROUNDING_D012_2026-07-09.md`](../../docs/workstreams/reviews/WS1_CRF_GROUNDING_D012_2026-07-09.md)

### Rule

| Do | Do not |
|---|---|
| State what the **form collected** | Imply “trial never collected X” when the CRF has a field for X |
| State what **PDS retains** (and at what precision) | Blame study design for public-extract reductions |
| Split gaps: CRF non-collection vs extract reduction vs programming scope | Invent values for null/stripped fields |

### Domain grounding summary (audit D-012)

| Domain | CRF form (examples) | What sponsor collected | What PDS extract retains | Limitation class |
|---|---|---|---|---|
| **AE** | Adverse Event Form `O.1_AE_1` | Diagnosis; status; grade; relationship to study treatment; action taken; corrective therapy; outcome (incl. fatal); seriousness Y/N + seriousness criteria | Terms/MedDRA; `AETOXGR` (incl. grade 5 fatal); `AEREL`/`AEACN`/`AECONTRT`/`AEOUT` largely populated; `AESER` + criteria flags largely present | **Class A** (core safety retained). **Class B** for **date precision** (CRF day/month/year → PDS week offsets `AESTWK`/`AEENWK`). Residual blank `AESER` on a minority of rows = null/incomplete, not “column never collected” |
| **LB** | Hematology `LABH_1`, Biochemistry `LABB_1`, PSA | CBC panel; electrolytes (Na/K/Cl/bicarb); LFTs; creat/BUN; glucose; testosterone; PSA | Matching `LBTESTCD` set including `SODIUM`,`K`,`CL`,`BICARB`,`ALP`,`CREAT`,`PSA`, etc. | **Class A** — electrolytes are **on CRF and in extract** (not a TROPIC “electrolyte never collected” story) |
| **ECOG** | VS panel ECOG 0–4 | Performance status 0–4 | `VSTESTCD=ECOG` with observed 0–4 | **Class A** |
| **DS** | End of Treatment `O.ENDTT_2`; End of Study `O.ENDST_1` | Main reason for stopping treatment/study (progression, AE, completed, LTFU, subject request, death, other, …) | `DSCAT`/`DSSCAT`/`DSDECOD`/`DSTERM` carry those concepts | **Class A** for reason concepts present in extract |

**Explicit non-claims:** full aCRF annotation package; day-true AE onset dates in public extract; commercial filing CRF provenance.

### Package domain scope (analysis-scoped SDTM)

| Layer | Content |
|---|---|
| **Pristine PDS (local)** | 34 `*.sas7bdat` domains (incl. EG, MH, PE, SV, IE, CD, CX, trial design fragments, etc.) |
| **Package / `define_sdtm.xml`** | **18** datasets: DM, EX, AE, LB, CM, DS, VS, LS, PN + SUPPAE/CM/DM/DS/EX/LB/LS + **TA, TS** |

Domains present in PDS but **not** packaged (by design for this Path A analysis package):
`CD, CX, EG, IE, MH, PE, PR, SC, SV, TE, TI, TV` (+ related SUPP*).
Do **not** claim the Module 5 SDTM folder is a full copy of every PDS domain.

**Full E2E audit:** [`docs/workstreams/reviews/WS1_SDTM_E2E_AUDIT_2026-07-09.md`](../../docs/workstreams/reviews/WS1_SDTM_E2E_AUDIT_2026-07-09.md)

### Material extract residuals (SDTM E2E)

| ID | Finding | Honesty |
|---|---|---|
| **F-028** | One subject has `EXTRT=XRP6258` (10 rows) while **all** DM rows are `ARM=MITOXANTRONE/PREDNISONE` | Arm authority = **DM/ADSL**, not EXTRT alone; do not silently re-code EX |
| **AE coverage** | AE subjects **357/371** (14 subjects with no AE rows) | Any-AE rates must use ADSL denominator |
| **F-026** | ~1134 BASELINE AE skeleton rows (blank AESER) | TEAE analyses use `TRTEMFL` |

---

## 1. Source data normalization & integrity controls

Source data are the official **Sanofi de-identified SDTM** for NCT00417079 (2013), accessed via **Project Data Sphere (PDS)** as SAS `*.sas7bdat`. Provenance: root README · [`00_governance/REPRODUCIBILITY.md`](../../00_governance/REPRODUCIBILITY.md).

Staging: [`L_staging_ingest.sas`](../../04_analysis_datasets/programs/sas/L_staging_ingest.sas) (and R twin `v_staging_ingest.R`) ingests `realsdtm.<domain>`, transpose-merges SUPP--, and coerces character continuous indicators to numeric where required.

> [!IMPORTANT]
> **Single-arm source limitation (Path A critical):** PDS public data here is **MP only (N=371)**. Cabazitaxel is **not** present as source SDTM. Dual-language ADaM recon is MP-only. Synthetic/reconstructed CbzP is merged only at TFL reporting ([`tfl_generation.R`](../../05_outputs/tfl/tfl_generation.R)) — non-confirmatory (F-003). Do not describe this as a clean two-arm double-programming of trial IPD.

### Database write-protection architecture

- `realsdtm` libref → `01_source_data/real_sdtm/` with `access=readonly` in [`00_config.sas`](../../04_analysis_datasets/programs/sas/00_config.sas)
- `staging` libref → `04_analysis_datasets/staging/`, writable and fully regenerable for SUPP-merged intermediates during SAS/ODA runs; the R twin writes domain `*.rds` files to the same governed staging zone
- Final ADaM products write under `04_analysis_datasets/adam/`; no program writes derived intermediates into the immutable source directory


---

## 2. SDTM Domain Mapping Summary
Standard SDTM mapping structures were built in `S_sdtm_mapping.sas` from trial-era **SDTM-IG 3.1.1** source data; SAP v4.0 treats this as source provenance and requires the release package to use the governed SDTMIG 3.4 uplift layer:
* **DM (Demographics):** Unique subject identifier `USUBJID` constructed via `STUDYID || '-' || SITEID || '-' || SUBJID`. Randomization date `RANDDT` and treatment start date `TRTSDT` mapped to standard ISO 8601 date fields.
* **EX (Exposure):** Normalised cycle-level actual administered doses (`EXDOSE` in mg).
* **AE (Adverse Events):** Coded utilizing MedDRA dictionaries into `AEDECOD`, `AEBODSYS`, and CTCAE-style grades (`AETOXGR`). **CRF grounding (D-012):** the Adverse Event form collected seriousness, relationship to study treatment, action taken, outcome (incl. fatal), and seriousness criteria — and those concepts are **largely present** in the PDS extract (`AESER`, `AEREL`, `AEACN`, `AEOUT`, `AESxxx` flags). Do **not** narrate “trial never collected seriousness.” **Date Precision Note (Class B reduction):** CRF collected calendar day/month/year; the public extract commonly carries week-offset integers (`AESTWK`, `AEENWK`). When a complete date is unavailable, analysis dates are reconstructed as `RFSTDTC + (week - 1) * 7` and retain the corresponding week-precision limitation. ADSL death dating preferentially uses a complete source `AEDTHDTC` when available and uses the DS week reconstruction only as fallback. This is an **extract design / de-identification property**, not a programming artefact.
* **LB (Laboratory):** Mapped continuous Absolute Neutrophil Count (ANC) and Prostate Specific Antigen (PSA) measurements.
* **DS (Disposition):** Captured study completion reasons, trial exits, and survival follow-up records.
* **Disposition-derived clinical signal:** DS progression records may be retained as a separately typed `CLINPROG` analysis signal, and DS death records support survival follow-up. `CLINPROG` is not a RECIST assessment and does not feed BOR, ORR, TTUMOR, or PFS.

---

## 3. Reference Ranges & Baseline Criteria
* ADSL and ADLB laboratory baselines use deterministic source records flagged `LBBLFL='Y'`; they are not replaced by an arbitrary missing-day or population-constant baseline.
* Normal reference ranges (`LBNRLO` and `LBNRHI`) were preserved from raw PDS metadata. Lab values outside these ranges are flagged accordingly in `LBNRIND`.

---

## 4. Known Data Limitations & Derivation Decisions

### 4.1 Baseline Laboratory Missingness
ADSL carries observed `PSABL`, `ALPBL`, and `HGBBL` values from source records flagged `LBBLFL='Y'`; a missing source baseline remains missing. No population-median proxy is inserted. `ALBBL` and `LDHBL` are unavailable in the public source release and remain missing with blank imputation flags. `ECOGBLIF`, `PSABLIF`, `ALPBLIF`, and `HGBBLIF` are `'N'` because the real-data track performs no imputation.

These variables are not efficacy-model covariates. The primary and secondary Cox/log-rank analyses stratify only on pooled observed randomization factors (`ECOGBL` 0–1 vs 2 and `MEASDISF`; see `05_outputs/tfl/tfl_generation.R`, `compute_tte_stats()` → `strata(ECOGBLGRP, MEASDISF)`).

### 4.2 Supplemental Domain Ingestion
Domains `LS` (Lesion) and `PN` (Pain/Numeric) do not have supplemental (`SUPPLS`, `SUPPPN`) datasets in the PDS source data. The `%transpose_supp()` macro gracefully handles this via the `supp_exists = 0` guard path, copying the primary domain directly without SUPP merge.

### 4.3 Country and Region Assignment
The DM domain in the source data does not contain country-of-study-site information. `COUNTRY` and `REGION` are **not present** in the de-identified release and are **not derived** (see the note in `B_bimo_generation.sas`); no placeholder geography is assigned. Geographic subgroup analyses are not part of SAP v4.0 reporting and are not reported.

### 4.4 Hardcoded Demographic Constant (SEX = 'M')
The demographics domain (`DM`) contains a hardcoded variable `SEX = 'M'` assigned to all subjects in `A_adsl_generation.sas`. This is a clinical decision consistent with the trial protocol for metastatic castration-resistant prostate cancer (mCRPC), which is an exclusively male patient population. To ensure metadata conformity, the Define-XML codelist references are maintained; however, no female subjects are present in the analysis dataset.

### 4.5 Partial/Imprecise Source Date Values (CM, LB, LS, PN)
The independent R SDTM validation (`04_analysis_datasets/programs/r/v_sdtm_validation.log`) raises four `[WARNING]`s flagging partial or imprecise ISO-8601 date values in source date fields: `CMSTDTC` (CM), `LBDTC` (LB), `LSDTC` (LS), and `PNDTC` (PN) — e.g. `----07`, `--12-26`, `2009---04`. These are expected manifestations of the public-release date precision. Values are preserved rather than assigned fabricated day precision; derivations requiring a complete calendar date accept only parseable complete dates or use a separately governed fallback (for example the SV hierarchy in F-042). The warnings therefore remain visible and their downstream exclusions/fallbacks are reviewable.

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
- **Rule-level disposition matrix (WS-1):** [`docs/workstreams/WS1_CORE_RESIDUAL_MATRIX.csv`](../../docs/workstreams/WS1_CORE_RESIDUAL_MATRIX.csv) — filed; still not a “CORE clean” claim.

**Related residual:** week-offset / partial ISO dates — **F-017** (§2 AE note, §4.5). Never invent day precision.

**Pinnacle 21 commercial ADaM/SDTM:** **NOT_AVAILABLE** under Path A (see WS-3 external validation index). Local CORE + dual-language ADaM recon are substitutes only.
