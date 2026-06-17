# Analysis Traceability Matrix

**Study:** TROPIC (EFC6193 / XRP6258) · NCT00417079
**Standards:** SDTMIG v3.1.1 (source) · ADaMIG v1.3 / OCCDS v1.0 + custom episode-merging (analysis)
**Purpose:** End-to-end traceability from source SDTM → ADaM (dual-programmed) → Define-XML
metadata → TFL output, plus the reconciliation evidence for each analysis dataset. This is
the single index a reviewer uses to walk any number on a table back to the code and the
source domains that produced it.

> **Scope reminder.** The reconciled `*_v.xpt` / `*_prod.xpt` deliverables contain the
> **real Mitoxantrone (MP) arm only (N=371)**. The synthetic, illustrative Cabazitaxel
> (CbzP) arm is merged for TFL demonstration only and is **never** part of the reconciled
> ADaM. SAS↔R parity is meaningful only for runs whose recorded `sas_execution_mode`
> (in `06_telemetry/pipeline_health.json`) is `oda` or `local` — see ADRG §6.

---

## 1. Source SDTM → Staging

| Step | Production (SAS) | Validation (R) | Output | Source domains |
|---|---|---|---|---|
| Staging ingest + SUPP-- transpose/merge | `02_production_sas/L_staging_ingest.sas` | `03_validation_r/v_staging_ingest.R` | `01_raw_source/real_sdtm/staging/*.rds` (R) / `staging.*` (SAS) | DM, EX, DS, VS, LB, LS, PN, CM, AE (+ SUPP--) |
| SDTM structural validation | — | `03_validation_r/v_sdtm_validation.R` | `v_sdtm_validation.log` | all consumed domains |

Date-precision note (applies downstream): AE and disposition timing are carried in the
source as **week offsets** and reconstructed as `RFSTDTC + (xxWK − 1) × 7` (±3.5 days).
OS / PFS / TTSAE / TTPSA / TTUMOR inherit this limitation (SDRG §2).

---

## 2. ADaM Datasets → Programs → Metadata → Reconciliation

| ADaM | Production (SAS) | Validation (R) | Define-XML | Key derivations (SAP ref) | Recon key | Recon status source |
|---|---|---|---|---|---|---|
| **ADSL** | `A_adsl_generation.sas` | `v_adsl_validation.R` | `IG.ADSL` | Populations ITTFL/SAFFL/PPROTFL; TRTSDT/TRTEDT (EX); DTHDT/LSTALVDT (DS, week-offset); ECOGBL (VS); MEASDISF/VISCFL (LS); PAINBL (PN, §6.x); baseline labs + **imputation flags `*IF`** (§6.3) | `USUBJID` (unique) | `reconciliation_status.json` |
| **ADEX** | `A_adex_generation.sas` | `v_adex_validation.R` | `IG.ADEX` | Cycle dose, CUMDOSE, NCYCLE, **RDI** (Project Optimus E-R proxy, §5.5) | `USUBJID,PARAMCD,AVISIT` (multiset) | ″ |
| **ADCM** | `A_adcm_generation.sas` | `v_adcm_validation.R` | `IG.ADCM` | Prior/concomitant meds; NACTDT (new anti-cancer therapy); docetaxel history | `USUBJID,CMSTDT,CMDECOD` (multiset) | ″ |
| **ADAE** | `A_adae_io_respec.sas` | `v_adae_io_validation.R` | `IG.ADAE` | TRTEMFL; **custom continuous-episode merging** (OCCDS v1.0 base; CQ02 hematologic irAE, ≤3-day gap, §5.2); AEOCCFL denominator flag; ATOXGR | `USUBJID,AESEQ` (unique) | ″ |
| **ADLB** | `A_adlb_generation.sas` | `v_adlb_validation.R` | `IG.ADLB` | Analysis windows (§5.6); ATOXGR baseline→worst shift; ANL01FL; ANCNADIR / ANCRECDY (§5.5) | `USUBJID,PARAMCD,AVISITN,LBDY` (multiset) | ″ |
| **ADRS** | `A_adrs_generation.sas` | `v_adrs_validation.R` | `IG.ADRS` | OVRLRESP (RECIST v1.0, §5.3); PSPROG (PCWG3, §5.4); OBJRESP / PSARESP | `USUBJID,PARAMCD,AVISIT` (multiset) | ″ |
| **ADTTE** | `A_adtte_generation.sas` | `v_adtte_validation.R` | `IG.ADTTE` | OS; PFS (NACT censoring hierarchy); **TTSAE** (was `TTOS`); TTPAIN; TTPSA; TTUMOR (measurable-disease subpop) | `USUBJID,PARAMCD` (multiset) | ″ |
| **CLINSITE** (BIMO) | `B_bimo_generation.sas` | `v_bimo_validation.R` | *(BIMO — not in ADaM define; documented in [BDRG](BDRG.md))* | Site-level roll-up of ADSL populations + ADAE safety: `N_RAND/N_SAF/N_ITT/N_PPROT/N_DEATH/N_SAE/N_TEAE` (per FDA BIMO TCG subset) | `STUDYID,SITEID` (unique) | ″ |

**Reconciliation engine:** `05_reconciliation/cross_lang_audit.R` (diffdf), **8 domains**.
"unique" keys give positional parity; "multiset" keys give keyed record-content parity (no
unique row id exists — ADRG §6). Both paths are unit-demonstrated in `tests/smoke_test.R`
(Cases A/B unique-key, Cases C/D keyless).

**Metadata conformance:** both `define.xml` (ADaM) and `define_sdtm.xml` pass XSD **and** parse in
the CDISC CORE reference engine (`Define_XML_Version 2.1.0`); each ADaM domain's structure/CT is
also checked by `06_telemetry/adam_conf_check.R` and the executable CORE rules in
`06_telemetry/conformance_rules/adam/` (traceable to ADaMIG; CORE_RUN_RECORD.md). `CLINSITE` is a
BIMO deliverable outside the ADaM define — its schema is asserted in `v_bimo_validation.R`.

---

## 3. TFL Outputs → SAP Section → Generator → ADaM Inputs

All TFLs are produced by `09_tfl/tfl_generation.R` (R / pharmaverse track, the reporting
deliverable). The numbers are the single source of truth; `ANALYSIS_REPORT.md` transcribes
them. SAS production-track copies of the statistical figures are rendered separately by
`02_production_sas/T_tfl_generation.sas` → `09_tfl/output/figures/sas/` (capability demo / visual QC).

| Output | SAP § | Generator function (`tfl_generation.R`) | Primary ADaM input(s) |
|---|---|---|---|
| `F-01-1_CONSORT_Disposition.png` | 3.x | CONSORT builder | ADSL (population flags) |
| `F-11-1_KM_OS.png` / `F-11-2_KM_PFS.png` | 5.1 | `compute_tte_stats()` → KM/Cox | ADTTE (OS, PFS) |
| `F-12-1_Subgroup_Forest.png` | 5.1 | subgroup Cox (`strata(ECOGBL, MEASDISF)`) | ADTTE + ADSL covariates |
| `F-13-1_PSA_Waterfall.png` | 5.4 | PSA best-change | ADRS / ADLB (PSA) |
| `F-14-1_Swimmer_Plot.png` | 5.x | exposure swimmer | ADEX, ADSL |
| `F-17-1_Optimus_Scatter.png` | 5.5 | LOESS E-R (RDI vs ANC nadir) | ADEX (RDI), ADLB (ANCNADIR) |
| `T-11-Efficacy_Tables.txt` | 5.1–5.4 | efficacy summary (KM/Cox/Fisher) | ADTTE, ADRS |
| `T-20-AE_Summary_Tables.txt` | 5.2 | TEAE summary | ADAE |
| `T-21-Lab_Shift_Tables.txt` | 5.6 | CTCAE shift | ADLB |

QC convention: the validated objects are the **analysis results behind each figure**
(survival functions, HRs, at-risk counts, response distributions), driven by the
SAS↔R-reconciled ADaM — not the rendered pixels.

**Analysis Results Metadata (ARM).** `07_define_xml/define.xml` carries ARM v1.0 ResultDisplays
that link key results to their ADaM data + method — the define-level complement to this matrix:

| ResultDisplay (define ARM) | Covers | This matrix's outputs |
|---|---|---|
| `RD.EFFICACY.SURVIVAL` | OS / PFS KM + Cox | `F-11-1`, `F-11-2`, `T-11` |
| `RD.EFFICACY.SECONDARY` | Secondary efficacy (TTPSA/TTUMOR, response) | `T-11`, `ADRS`-derived |
| `RD.SAFETY.TEAE` | TEAE summary | `T-20` |

> **ARM gap (honest):** the exploratory figure displays (`F-12` subgroup forest, `F-13` PSA
> waterfall, `F-14` swimmer, `F-17` Optimus) and the lab-shift table (`T-21`) do **not** yet have
> dedicated ARM ResultDisplay entries; their traceability is via this matrix + the generator
> functions above. Extending ARM to those displays is a documented follow-up.

---

## 4. Orchestration & Provenance

The pipeline is **15 stages** (`cibuild.py`); the BIMO domain inserted at Stage 10 shifted the
later stage numbers.

| Stage | Driver | Evidence artifact |
|---|---|---|
| 1–9 (staging + R ADaM validation) | `06_telemetry/cibuild.py` → `logrx::axecute(...)` | `03_validation_r/*.log` |
| 10 (R BIMO validation) | `v_bimo_validation.R` | `04_adam/clinsite_v.xpt` |
| 11 (SAS production) | `cibuild.py` (`local`/`oda`/`cached`/`sim`/`error`) | `pipeline_health.json` `sas_execution_mode` |
| 12 (cross-language reconciliation) | `cross_lang_audit.R` | `reconciliation_status.json` (**8 domains** incl. CLINSITE), `reconciliation_report.html` |
| 13 (TFL) | `tfl_generation.R` | `09_tfl/output/tables/*`, `09_tfl/output/figures/*` |
| 14 (numerical results reconciliation) | `results_reconcile.R` — SAS `PROC LIFETEST` vs R `survfit` (MP-arm KM medians / events / N) | `results_reconciliation_status.json` |
| 15 (eCTD Module 5 packaging) | `package_ectd.py` | `m5/` (ephemeral) |
| *(offline)* CDISC CORE conformance | `06_telemetry/run_core_conformance.sh` — SDTMIG-3.2 rules + executable ADaM rules (`conformance_rules/adam/`, `--local-rules`) | `06_telemetry/conformance/core_{sdtm,adam}_report.json`, `CORE_RUN_RECORD.md` |

Run reproducibility: R toolchain pinned by `renv.lock`; self-contained demo
(`python3 06_telemetry/cibuild.py --demo`) runs `tests/smoke_test.R` with no real data,
no SAS, no credentials. CORE conformance reproduction: `run_core_conformance.sh` (REPRODUCIBILITY.md §7).
