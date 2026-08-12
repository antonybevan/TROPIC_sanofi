# Analysis Traceability Matrix

| Field | Value |
|---|---|
| **Document** | Analysis Traceability Matrix |
| **Study** | TROPIC (EFC6193 / XRP6258) · NCT00417079 |
| **Standards** | SDTMIG v3.1.1 source → v3.4 uplift · ADaMIG v1.3 / OCCDS v1.0 + custom episode-merge |
| **Document version** | 2.0 (controlled release / catalog-aligned) |
| **Effective** | 2026-08-05 |
| **Product claim** | Controlled clinical-submission simulation (`docs/PRODUCT_CLAIM.md`) |
| **TFL control authority** | `config/tfl_output_catalog.yaml` |

**Purpose:** Walk any controlled display number back to code, ADaM, define, and recon evidence.

> **SAP v4.0:** Programming authority for analysis intent (`02_specifications/sap/…`). This matrix
> is **implementation** traceability for the controlled demo cut — not a sponsor filing lock.

> **Scope.** Reconciled `*_v.xpt` / `*_prod.xpt` = **real MP only (N=371)**. Synthetic CbzP is
> TFL-merge only (F-003). Dual-language recon is meaningful only when
> `sas_execution_mode` is `oda`/`local` (ADRG §6). Single-author tracks ≠ org GxP double programming.

**Companions:** [`ADRG.md`](ADRG.md) · [`SDRG.md`](SDRG.md) · [`BDRG.md`](BDRG.md) ·
[`WS5_KNOWN_DIFFERENCES_MEMO.md`](../../docs/workstreams/WS5_KNOWN_DIFFERENCES_MEMO.md)

---

## 1. Source SDTM → Staging

| Step | Production (SAS) | Validation (R) | Output | Source domains |
|---|---|---|---|---|
| Staging ingest + SUPP-- transpose/merge | `04_analysis_datasets/programs/sas/L_staging_ingest.sas` | `04_analysis_datasets/programs/r/v_staging_ingest.R` | `04_analysis_datasets/staging/*.rds` (R) / governed `staging.*` (SAS) | DM, EX, DS, VS, LB, LS, PN, CM, AE (+ SUPP--) |
| SDTM structural validation | — | `04_analysis_datasets/programs/r/v_sdtm_validation.R` | `v_sdtm_validation.log` | all consumed domains |

Date-precision note (applies downstream): AE and disposition timing commonly use source
**week offsets**, reconstructed as `RFSTDTC + (xxWK − 1) × 7`. Complete source dates are
preferred where available (notably `AEDTHDTC` for death); otherwise the week-derived value and
its precision limitation remain explicit. Partial ISO dates are never assigned fabricated day
precision (SDRG §2/§4.5).

---

## 2. ADaM Datasets → Programs → Metadata → Reconciliation

| ADaM | Production (SAS) | Validation (R) | Define-XML | Key derivations (SAP ref) | Recon key | Recon status source |
|---|---|---|---|---|---|---|
| **ADSL** | `A_adsl_generation.sas` | `v_adsl_validation.R` | `IG.ADSL` | Population flags inherited from DM; planned treatment from DM and actual treatment from qualifying administered IV EX; exact `AEDTHDTC` death preferred with DS-week fallback; last observed contact across DS/EX/VS/LB/LS/PN/SV, capped at death; component-specific 5-of-7 `PAINBL`; observed source baselines retained without constant imputation | `USUBJID` (unique) | `reconciliation_status.json` |
| **ADEX** | `A_adex_generation.sas` | `v_adex_validation.R` | `IG.ADEX` | Qualifying randomized IV exposure only; initial planned dose from `EXPDOSE`; cumulative administered dose from `EXCUMD2`; positive administered-cycle count; source `EXTRINT` RDI carried only when subject repetitions agree; delay/reduction counts | `USUBJID,PARAMCD,AVISIT` (unique) | ″ |
| **ADCM** | `A_adcm_generation.sas` | `v_adcm_validation.R` | `IG.ADCM` | Prior/concomitant meds; NACTDT (new anti-cancer therapy); docetaxel history; source `CMSEQ` retained | `USUBJID,CMSEQ` (unique) | ″ |
| **ADAE** | `A_adae_io_respec.sas` | `v_adae_io_validation.R` | `IG.ADAE` | TRTEMFL; **custom continuous-episode merging** (OCCDS v1.0 base; CQ02 hematologic irAE, ≤3-day gap, §7.7); AEOCCFL denominator flag; ATOXGR | `USUBJID,AESEQ` (unique) | ″ |
| **ADLB** | `A_adlb_generation.sas` | `v_adlb_validation.R` | `IG.ADLB` | Source `LBBLFL='Y'` baseline; analysis windows (§11.1.3); source `LBTOXGR` carried as ATOXGR (no independent re-grading); source `LBSEQ` retained on source rows; ANL01FL; ANCNADIR / ANCRECDY (§10); PSA typed as tumour marker and other categories carried from `LBCAT` | `USUBJID,PARAMCD,AVISITN,LBDY,LBSEQ` (unique) | ″ |
| **ADRS** | `A_adrs_generation.sas` | `v_adrs_validation.R` | `IG.ADRS` | Lesion-derived `OVRLRESP`; confirmed `BESTRESP`/`OBJRESP` with no intervening PD; reconstructed `PSPROG`/`PSARESP`; exploratory 2+2 `BSGRESP`; separately typed non-RECIST `CLINPROG`. Neither `BSGRESP` nor `CLINPROG` feeds BOR, ORR, TTUMOR, or PFS | `USUBJID,PARAMCD,ADT,AVISIT` (unique) | ″ |
| **ADTTE** | `A_adtte_generation.sas` | `v_adtte_validation.R` | `IG.ADTTE` | OS; PFS earliest typed lesion-derived tumour, reconstructed PSA, governed F-042 pain, or death event with earlier NACT censoring; TTSAE through the bounded 30-day safety window; ITT TTPAIN/TTPSA/TTUMOR with parameter-specific censoring and cutoff. Missing/pre-origin dates are release-blocking; no silent duration floor | `USUBJID,PARAMCD` (unique) | ″ |
| **CLINSITE** (BIMO) | `B_bimo_generation.sas` | `v_bimo_validation.R` | *(BIMO — not in ADaM define; documented in [BDRG](BDRG.md))* | Site-level roll-up of ADSL populations + ADAE safety: `N_RAND/N_SAF/N_ITT/N_PPROT/N_DEATH/N_SAE/N_TEAE` (per FDA BIMO TCG subset) | `STUDYID,SITEID` (unique) | ″ |

**Reconciliation engine:** `06_qc_evidence/reconciliation/cross_lang_audit.R` (diffdf), **8 domains**.
Every manifest business key is required to exist and be unique in both tracks before an exact
keyed comparison is allowed. Duplicate keys are release-blocking, and any differing cell is
persisted as a dataset/variable discrepancy artifact. Positive parity, injected-cell-difference,
and duplicate-key rejection paths are unit-demonstrated in `tests/smoke_test.R`.

**Metadata conformance:** both `define.xml` (ADaM) and `define_sdtm.xml` pass XSD **and** parse in
the CDISC CORE reference engine (`Define_XML_Version 2.1.0`); each ADaM domain's structure/CT is
also checked by `platform/adam_conf_check.R` and the executable CORE rules in
`platform/conformance_rules/adam/` (traceable to ADaMIG; CORE_RUN_RECORD.md). `CLINSITE` is a
BIMO deliverable outside the ADaM define — its schema is asserted in `v_bimo_validation.R`.

**Metadata control source (audit C-4 inversion).** The authoring-format ADaM specification
`03_metadata/adam/ADaM_spec.xlsx` (metacore/Pinnacle-21 workbook) is the upstream master that
*governs* the define and the data — not a rendering derived from the define. Two gates enforce the
direction: `03_metadata/define/check_define_conformance.R` (**spec → define**, with a drift-detecting
self-test) and `04_analysis_datasets/programs/r/spec_data_checks.R` (**spec → data** via metacore/metatools/xportr
against `04_analysis_datasets/adam/*_prod.xpt`). Both run as pipeline Stages 27–28 and in CI; reports in
`platform/conformance/spec_{define,data}_conformance.json`. The spec also drives the
variable-label artifacts for both tracks (`platform/gen_adam_labels.R`).

---

## 3. TFL outputs — controlled catalog alignment

**Authority:** `config/tfl_output_catalog.yaml` only.  
**Generator:** `05_outputs/tfl/tfl_generation.R` (reporting deliverable).  
**Not claimed:** full SAP Appendix D (18 IDs deferred with reasons).
**Regenerate local index (optional):** `python3 platform/build_tfl_output_index.py` (report is gitignored under portfolio surface policy).

### 3.1 Controlled in-scope (21 IDs)

| Catalog ID | File / delivery form | Primary ADaM | Notes |
|---|---|---|---|
| F-01-1 | `F-01-1_CONSORT_Disposition.png` | ADSL | Legacy CONSORT filename; population/mortality overview |
| F-11-1 | `F-11-1_KM_OS.png` | ADTTE OS | Primary OS KM |
| F-11-2 | `F-11-2_KM_PFS.png` | ADTTE PFS | Primary PFS KM |
| F-12-1 | `F-12-1_Subgroup_Forest.png` | ADTTE OS + ADSL | Forest HR recon gated |
| F-13-1 | `F-13-1_PSA_Waterfall.png` | ADLB PSA + ADSL | |
| F-14-1 | `F-14-1_Swimmer_Plot.png` | ADEX + ADSL | |
| F-17-1 | `F-17-1_Optimus_Scatter.png` | ADEX RDI + ADLB ANCNADIR | Synthetic/comparative caution |
| T-11-3 | inside `T-11-Efficacy_Tables.txt` | ADRS/ADLB + ADSL | PSA response rate; observed baseline PSA denominator |
| T-11-4 | inside `T-11-Efficacy_Tables.txt` | ADRS + ADSL | Confirmed ORR per RECIST v1.0; measurable-disease denominator |
| T-11-5 | inside `T-11-Efficacy_Tables.txt` | PN/SV + ADSL | Pain response; CbzP explicitly N/A where PN is unavailable |
| T-11-6 | inside `T-11-Efficacy_Tables.txt` | ADTTE TTUMOR | Catalog ID ≠ separate file per row |
| T-11-7 | inside `T-11-Efficacy_Tables.txt` | ADTTE TTPSA | |
| T-11-8 | inside `T-11-Efficacy_Tables.txt` | ADTTE TTPAIN | Time to pain progression; randomization origin |
| T-11-8b | inside `T-11-Efficacy_Tables.txt` | ADRS | ORR response-evaluable sensitivity; explicit extension |
| T-17-1 | inside `T-17-Optimus_Tables.txt` | ADEX | RDI categories |
| T-17-2 | inside `T-17-Optimus_Tables.txt` | ADLB + ADEX | ANC nadir by G-CSF |
| T-17-4 | inside `T-17-Optimus_Tables.txt` | ADEX/ADLB/ADTTE | Benefit–risk by RDI tertile |
| T-20-1 | inside `T-20-AE_Summary_Tables.txt` | ADAE | TEAE summary |
| T-20-2 | inside `T-20-AE_Summary_Tables.txt` | ADAE | Grade ≥3 by SOC |
| T-21-1 | inside `T-21-Lab_Shift_Tables.txt` | ADLB | CTCAE shift MP |
| T-21-2 | inside `T-21-Lab_Shift_Tables.txt` | ADLB | CTCAE shift CbzP (synthetic arm display) |

### 3.2 Explicitly deferred (18 IDs) — sample of policy

Not listed above = **not** controlled delivery scope. Examples: standalone T-11-1/T-11-2 OS/PFS table shells (evidence via F-11-1/F-11-2 + results reconciliation instead), F-12-2, T-12-*, and many T-20 detail shells. Full list and reasons: `config/tfl_output_catalog.yaml` → `deferred_not_in_scope`.

### 3.3 SAS companion figures (out of DAG)

SAS PNGs under `05_outputs/tfl/output/figures/sas/` / package `figures/sas/` are **capability demos**
(`platform/_oda_render_tfl.py`, outside `study_manifest` spine). Inventories may hash them; they
do **not** gate controlled-scope completeness. Linked primary IDs: F-11-1, F-11-2, F-12-1, F-13-1, F-14-1, F-17-1.

### 3.4 QC convention

Validated objects are the **analysis results behind each figure/table** (driven by reconcilable
ADaM and figure-data/forest gates when exports exist) — not pixel identity.

**Listings:** none in controlled scope (prior L-01 discontinuation placeholder removed — F-004).

**Analysis Results Metadata (ARM).** `03_metadata/define/define.xml` carries ARM v1.0 ResultDisplays
that link key results to their ADaM data + method — the define-level complement to this matrix:

| ResultDisplay (define ARM) | Covers | This matrix's outputs |
|---|---|---|
| `RD.EFFICACY.SURVIVAL` | OS / PFS KM + Cox | `F-11-1`, `F-11-2`, `T-11` |
| `RD.EFFICACY.SECONDARY` | ITT secondary TTE analyses (TTPSA/TTUMOR/TTPAIN) | `T-11-6`, `T-11-7`, `T-11-8` |
| `RD.EFFICACY.RESPONSE` | PSA, objective and pain response plus ORR sensitivity | `T-11-3`, `T-11-4`, `T-11-5`, `T-11-8b` |
| `RD.SAFETY.TEAE` | TEAE summary | `T-20` |
| `RD.EFFICACY.SUBGROUP` | OS treatment-effect subgroup hazard ratios | `F-12-1` |
| `RD.EFFICACY.PSA.RESPONSE` | PSA best % change from baseline | `F-13-1` |
| `RD.SAFETY.EXPOSURE` | Treatment exposure duration / cycles | `F-14-1` |
| `RD.OPTIMUS.ER` | Project Optimus RDI vs ANC-nadir exposure-response | `F-17-1` |
| `RD.OPTIMUS.TABLES` | RDI distribution, ANC/G-CSF and descriptive benefit-risk | `T-17-1`, `T-17-2`, `T-17-4` |
| `RD.SAFETY.LABSHIFT` | CTCAE grade shift, baseline → worst | `T-21-1`, `T-21-2` |

> **ARM coverage (2026-08-04).** ARM now spans **10 ResultDisplays / 18 AnalysisResults**.
> Every controlled analysis output is mapped to a ResultDisplay except the analysis-population
> flow diagram `F-01-1`, which is not a statistical analysis result. The response display
> records the staged PN/SV dependency for T-11-5 and its exact subject-level
> `F042_PAIN_RESPONSE` SAS/R control; all ResultDisplays carry the controlled synthetic-comparator
> disclosure. Referential integrity and endpoint semantics are gated by
> `validate_define.py`, `define_arm_contract.py`, and G02. The analysis-population overview (`F-01`, legacy
> `CONSORT` filename) and the
> discontinuation listing is intentionally **out of scope** (F-004 removed; no listing in
> `config/tfl_output_catalog.yaml` controlled scope). Flow diagram `F-01-1` is out of ARM scope.

---

## 4. Orchestration & Provenance

The pipeline is a **manifest-driven full DAG** (`config/study_manifest.yaml` → `cibuild.py`;
stage count includes G00/G02/G07 locks + admiral + figure-data recon + packaging — see live
`pipeline_health.json` / `stages_expected`). Includes third-engine **admiral**, TFL/catalog
controls, eCTD backbone/materialize, log cleanliness, and release-run manifest binding.

| Stage band | Driver | Evidence artifact |
|---|---|---|
| Pre + R ADaM/BIMO validation | `cibuild.py` → `logrx` / rscript | `04_analysis_datasets/programs/r/*.log`, `04_analysis_datasets/adam/*_v.xpt` |
| SAS production | `cibuild.py` (`local`/`oda`/`cached`/`sim`) | `pipeline_health.json` `sas_execution_mode` |
| Cross-language reconciliation | `cross_lang_audit.R` | `reconciliation_status.json` (**8 domains**), HTML report |
| Admiral T1 track (ADSL, OS/PFS) | `admiral_*.R` + `admiral_reconcile.R` | `admiral_reconciliation_status.json` |
| TFL + results/forest recon | `tfl_generation.R`, `results_reconcile.R`, `forest_reconcile.R` | `05_outputs/tfl/output/`, recon status JSON |
| Spec conformance + package | define/data checks, eCTD, log gate, release manifest | `platform/*`, `08_submission_package/m5/`, `08_submission_package/ectd/0000/` |

Stage numbers are **manifest-derived** (not hard-coded). Optional local gate map:
`python3 platform/build_orchestrator_gate_map.py` (generated report is gitignored).

| Stage | Control | Evidence artifact |
|---|---|---|
| 14–16 (synthetic reconstruction/validation/export) | `reconstruct_cbzp_arm.R`, `guyot_validation_report.R`, `export_cbzp_xpt.R` | regenerated comparator RDS/XPT and validation report |
| 17 (real SAS production) | `00_master_driver.sas` through the ODA broker | production XPTs, SAS logs, companion TFL evidence |
| 18 (cross-language audit) | `cross_lang_audit.R` | `reconciliation_status.json`, reconciliation report |
| 19 (admiral ADSL) | `admiral_adsl.R` | third-engine ADSL derivation evidence |
| 20 (admiral ADTTE OS/PFS) | `admiral_adtte.R` | third-engine TTE derivation evidence |
| 21 (admiral core reconciliation) | `admiral_reconcile.R` | `admiral_reconciliation_status.json` |
| 22 (synthetic comparator bridge parity) | `check_cbzp_bridge.R` | CBZP RDS/XPT bridge parity status |
| 23 (TFL) | `tfl_generation.R` | `05_outputs/tfl/output/tables/*`, `05_outputs/tfl/output/figures/*` |
| 24 (numerical results reconciliation) | `results_reconcile.R` — SAS `PROC LIFETEST` vs R `survfit` (MP-arm KM medians / events / N) | `results_reconciliation_status.json` |
| 25 (forest-HR reconciliation) | `forest_reconcile.R` | figure-driving subgroup HR reconciliation status |
| 26 (figure-data reconciliation) | `figure_data_reconcile.R` | figure-driving SAS/R data parity status |
| 27 (spec → define conformance) | `03_metadata/define/check_define_conformance.R` — `define.xml` checked against `ADaM_spec.xlsx` (C-4 inversion; `--self-test` proves drift detection) | `platform/conformance/spec_define_conformance.json` |
| 28 (spec → data conformance) | `04_analysis_datasets/programs/r/spec_data_checks.R` — metacore/metatools/xportr vs `04_analysis_datasets/adam/*_prod.xpt` | `platform/conformance/spec_data_conformance.json` |
| 29 (reviewer package lock) | `check_gate_g07_reviewer_package.py` | G07 reviewer-package status |
| 30 (Dataset-JSON v1.1 export) | `export_datasetjson.py` | `04_analysis_datasets/datasetjson/**/*.json` (ephemeral) |
| 31 (Analysis Results Standard v1.0) | `build_ars.py` | `05_outputs/ars/` (ephemeral) |
| 32 (USDM v3.0 study definition) | `build_usdm.py` | `03_metadata/usdm/tropic_usdm.json` (also a data-free CI gate) |
| 33 (eCTD Module 5 packaging) | `package_ectd.py` | `08_submission_package/m5/` |
| 34 (eCTD backbone + STF, sequence 0000) | `build_ectd_backbone.py` | `08_submission_package/ectd/0000/index.xml`, `index-md5.txt`, `stf-tropic.xml` |
| 35 (materialize eCTD sequence + MD5 re-verify) | `materialize_ectd.py` | `08_submission_package/ectd/0000/` leaves (every leaf MD5-verified) |
| 36 (log cleanliness) | `check_log_cleanliness.py` | configured persisted log cleanliness status |
| 37 (release manifest binding) | `build_release_run_manifest.py` | `release_run_manifest.json`, release grade |
| *(offline)* CDISC CORE conformance | `platform/run_core_conformance.sh` — SDTMIG **3.4** rules on the uplifted layer (authoritative) + SDTMIG 3.2 baseline on the pristine 3.1.1 source + executable ADaM rules (`conformance_rules/adam/`, `--local-rules`) | `platform/conformance/core_sdtm34_report.json` + `core_{sdtm,adam}_report.json`; `CORE_SDTM34_RUN_RECORD.md`, `CORE_RUN_RECORD.md` |

Run reproducibility: R toolchain pinned by `renv.lock`; self-contained demo
(`python3 platform/cibuild.py --demo`) runs `tests/smoke_test.R` with no real data,
no SAS, no credentials. CORE conformance reproduction: `run_core_conformance.sh` (00_governance/REPRODUCIBILITY.md §7).
