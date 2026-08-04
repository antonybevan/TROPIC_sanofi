# TROPIC Script Map — What Runs, What Doesn’t, How to Learn

**Purpose:** Stop reverse-engineering a junk drawer.  
**Authority:** `config/study_manifest.yaml` + `platform/cibuild.py`  
**Claim:** Path A demo (`docs/PRODUCT_CLAIM.md`)  
**Date:** 2026-07-09

If a file is not listed here as CORE or clearly SUPPORT, treat it as **secondary** until proven otherwise.

---

## 0. How to fix the “everything looks like junk” problem

| Wrong approach | Right approach |
|---|---|
| Open `platform/` and try to read every `.py` | Read this map → then **only CORE** files |
| Assume every file is production | Tier files: CORE / SUPPORT / REPORT / ARCHIVE |
| Delete half the repo in panic | Classify first; delete only confirmed dead |
| Learn random folders | Learn in **pipeline order** (section 2) |

**Hard rule:**  
`study_manifest.yaml` is the shopping list.  
`cibuild.py` is the runner.  
Anything not on that list is not the main spine.

---

## 1. The whole system in 8 boxes

```text
[1] SOURCE
    01_source_data/real_sdtm/     (local only — not in git)
        │
[2] SPEC + METADATA
    02_specifications/sap/SAP v4.0
    03_metadata/adam/ADaM_spec.xlsx
    03_metadata/define/
        │
[3] BUILD ADaM  (dual language)
    SAS: 04_analysis_datasets/programs/sas/A_*.sas  (+ master driver)
    R:   04_analysis_datasets/programs/r/v_*.R
        │
[4] RECONCILE
    06_qc_evidence/reconciliation/cross_lang_audit.R
    admiral_* + admiral_reconcile.R
    results_reconcile.R · forest_reconcile.R
        │
[5] TFL
    05_outputs/tfl/tfl_generation.R
        │
[6] PACKAGE
    platform/package_ectd.py → 08_submission_package/m5/
        │
[7] SEAL
    build_release_run_manifest.py · verify_release.py
        │
[8] SHOW
    08_submission_package/m5/  +  07_reviewer_explanation/guides/
```

**That’s the project.** Everything else is either support for one box, or noise.

---

## 2. How to reverse-engineer (order that actually works)

Do **not** start in `platform/`.

| Day | Open only this | Goal |
|---:|---|---|
| **1** | `docs/PRODUCT_CLAIM.md` · `08_submission_package/m5/` · guides | What the product is |
| **2** | `config/study_manifest.yaml` (full file) | What is *supposed* to run |
| **3** | `platform/cibuild.py` (how it loads stages) | How the list becomes a run |
| **4** | One pair: `A_adsl_generation.sas` + `v_adsl_validation.R` | How dual-language works |
| **5** | `cross_lang_audit.R` | How PASS is proven |
| **6** | `admiral_adsl.R` + `admiral_reconcile.R` | Third engine |
| **7** | `tfl_generation.R` + `config/tfl_output_catalog.yaml` | Outputs |
| **8** | `package_ectd.py` | How `m5/` is assembled |
| **9** | `scripts/verify_release.py` | What “sealed” means |

After day 4 you can already explain 70% of the biometrics story.

---

## 3. CORE — on the DAG (this is “used”)

Single button: `python3 platform/cibuild.py`

### 3.1 Pre stages

| Script | Job |
|---|---|
| `platform/check_gate_g00_governance.py` | Claim / scope lock |
| `platform/check_gate_g02_specification.py` | SAP / spec lock |
| `platform/gen_adam_labels.R` | Labels/order from ADaM spec |
| `04_analysis_datasets/programs/r/v_staging_ingest.R` | Stage SDTM |
| `04_analysis_datasets/programs/r/v_sdtm_validation.R` | SDTM checks |

### 3.2 Per-dataset ADaM (SAS + R pairs)

| Dataset | SAS (production) | R (validation) |
|---|---|---|
| ADSL | `A_adsl_generation.sas` | `v_adsl_validation.R` |
| ADEX | `A_adex_generation.sas` | `v_adex_validation.R` |
| ADCM | `A_adcm_generation.sas` | `v_adcm_validation.R` |
| ADAE | `A_adae_io_respec.sas` | `v_adae_io_validation.R` |
| ADLB | `A_adlb_generation.sas` | `v_adlb_validation.R` |
| ADRS | `A_adrs_generation.sas` | `v_adrs_validation.R` |
| ADTTE | `A_adtte_generation.sas` | `v_adtte_validation.R` |
| clinsite | `B_bimo_generation.sas` | `v_bimo_validation.R` |

SAS batch entry (called when real SAS runs): `00_master_driver.sas`  
Helpers included by SAS (not separate DAG rows): `00_config.sas`, `L_staging_ingest.sas`, `S_sdtm_mapping.sas`, `U_xpt_export.sas`, `_adam_labels.sas`

### 3.3 Post stages

| Script | Job |
|---|---|
| `06_qc_evidence/reconciliation/cross_lang_audit.R` | SAS↔R cell recon |
| `04_analysis_datasets/programs/r/admiral_adsl.R` | Third-engine ADSL |
| `04_analysis_datasets/programs/r/admiral_adtte.R` | Third-engine OS/PFS |
| `06_qc_evidence/reconciliation/admiral_reconcile.R` | admiral vs prod |
| `01_source_data/check_cbzp_bridge.R` | Synthetic CbzP parity |
| `05_outputs/tfl/tfl_generation.R` | Main TFL suite |
| `06_qc_evidence/reconciliation/results_reconcile.R` | Stats recon |
| `06_qc_evidence/reconciliation/forest_reconcile.R` | Forest HR recon |
| `06_qc_evidence/reconciliation/figure_data_reconcile.R` | Figure-driving data recon (skip if no SAS exports) |
| `03_metadata/define/check_define_conformance.R` | Spec→define |
| `04_analysis_datasets/programs/r/spec_data_checks.R` | Spec→data |
| `platform/check_gate_g07_reviewer_package.py` | Guides/claim lock |
| `platform/export_datasetjson.py` | Dataset-JSON export |
| `platform/build_ars.py` | ARS export |
| `platform/build_usdm.py` | USDM export |
| `platform/package_ectd.py` | Build `m5/` |
| `platform/build_ectd_backbone.py` | eCTD index/STF |
| `platform/materialize_ectd.py` | Sequence materialize |
| `platform/check_log_cleanliness.py` | Log gate |
| `platform/build_release_run_manifest.py` | Hash seal |

**~40 orchestrated steps. That is the spine.**

---

## 4. SUPPORT — used, but not “the science”

| Script | When you need it |
|---|---|
| `platform/cibuild.py` | Always (runner) |
| `platform/manifest.py` | Loaded by cibuild |
| `platform/oda_broker.py` · `seed_sdtm.py` | Real ODA SAS only |
| `platform/generate_config.py` | Regen SAS config from YAML |
| `platform/_oda_render_tfl.py` | Manual SAS figure diagnostic (release DAG uses `cibuild.py` Stage 14) |
| `scripts/verify_release.py` | Re-check seals |
| `01_source_data/reconstruct_cbzp_*.R` · `export_cbzp_xpt.R` | Build synthetic arm (manual / pre-req) |
| `04_analysis_datasets/programs/r/config_study.R` · `load_spec.R` · `activate_renv.R` | Shared R helpers |
| `05_outputs/tfl/tfl_stats.R` · `lab_shift_table.R` | Sourced by TFL suite |

---

## 5. CONTROL REPORTS — not junk, but not the product

These **regenerate markdown/CSV status**. They do **not** derive ADSL.

Examples:

- `build_delivery_dashboard.py`
- `build_tfl_output_index.py`
- `build_metadata_control_report.py`
- `build_validation_strategy_report.py`
- `build_orchestrator_gate_map.py`
- `build_source_profile.py`
- `build_ctq_traceability_report.py`
- `build_delivery_controls.py` (runs a suite of the above)
- `build_release_candidate_checklist.py`

**How to treat them:**  
Ignore while learning biometrics. Use only when checking delivery/control status.

---

## 6. Known non-spine / stale-ish (from orphan register)

Source of truth for this section:  
`06_qc_evidence/audit/orphans_dangling_deadcode.csv`

| Item | Status | What to do |
|---|---|---|
| `figure_data_reconcile.R` | **On DAG** (after forest); `not_available` if SAS figure CSVs absent | Keep; re-run full DAG to refresh seal stage list |
| SAS `T_tfl_generation.sas` + `_oda_render_tfl.py` | TFL program is in the real-SAS DAG; `_oda_render_tfl.py` is manual diagnostic-only | Classified in `platform/README.md` |
| Dataset-JSON / ARS / USDM outputs | Built on DAG; **not** eCTD primary path | CLASSIFIED_ADDITIVE (folder READMEs) |
| `tools/archive/**` | Dead / one-time / migration | Do not run as prod |
| Manual CbzP reconstruct scripts | Pre-req, not every DAG tick | Documented; bind hashes on release |
| 18 deferred TFLs in catalog | Explicitly **not in scope** | Not “missing bugs” — deferred by control |

**Done vs not done is not “count files.”** It is:

| Done (Path A seal) | Not done / deferred |
|---|---|
| Dual-lang ADaM + recon on MP | Org GxP double programming |
| admiral core (ADSL, OS, PFS) | Full admiral every domain |
| Controlled TFL set (21 in catalog) | 18 deferred SAP TFLs |
| Module 5 style package + seals | Real FDA app IDs / filing |
| Findings dispositioned | Full commercial P21 clearance |

Board: `docs/WORKSTREAM_EXECUTION_BOARD.md`  
Deferred TFLs: `config/tfl_output_catalog.yaml`

---

## 7. Fix plan (how we clean this without burning it down)

### Phase A — Connect the dots ✅

1. This map (`docs/SCRIPT_MAP.md`)  
2. Root README dual surface (package vs factory)  
3. `docs/INDEX.md` three tours  

### Phase B — Label the factory ✅ (2026-07-09 cleanup)

1. `platform/README.md` tiers: CORE_DAG · SUPPORT · REPORT · LAB  
2. Confirmed dead → `tools/archive/`  
3. `figure_data_reconcile.R` wired on DAG + graceful `not_available`  
4. Additive layers labeled (Dataset-JSON / ARS / USDM READMEs)  
5. Orphan register statuses updated  

**Success:** opening `platform/` has a triage map; dead code not next to live programs.

### Phase C — Portfolio surface (git hygiene) ✅

1. `docs/REPO_SURFACE_POLICY.md` + `docs/INTERVIEWER_GUIDE.md`  
2. `.gitignore` seal allowlist; untrack regenerable reports / inventory dumps  
3. Dead code local under `tools/archive/` (gitignored, not portfolio)  
4. Optional later: split `platform/` subfolders; re-seal after real full DAG  

**Success:** bare clone shows package + claim + seals — not a status-JSON landfill.

### What we will **not** do

- Big-bang rewrite of ADaM programs for “cleanliness”  
- Renaming `00_…08_` again before the map is used  
- Claiming “fixed” by writing more YAML without removing confusion  

---

## 8. One-screen cheat sheet

```text
LEARN / DEMO
  claim → m5/ → guides

SPINE
  study_manifest.yaml
  cibuild.py
  A_*.sas + v_*.R
  cross_lang_audit.R
  admiral_* + recon
  tfl_generation.R
  package_ectd.py
  verify_release.py

IGNORE WHILE LEARNING
  most build_*_report.py
  most docs/*_REPORT.md
  studies/DEMO02
  shiny
  Dataset-JSON/ARS/USDM deep dives
```

---

## 9. When you’re lost

Ask only:

1. **Is it on the DAG?** → `study_manifest.yaml`  
2. **Is it CORE biometrics?** → A_/v_ programs + recon  
3. **Is it the product face?** → `08_submission_package/m5/`  
4. **Is it a status printer?** → ignore for learning  

If none of those — it’s secondary. Don’t let it steal your attention.
