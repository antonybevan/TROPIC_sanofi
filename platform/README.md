# `platform/` — Factory control plane

**Audience:** engineers only.  
**Not the product.** Reviewers open `08_submission_package/m5/`.  
**Spine map:** [`docs/SCRIPT_MAP.md`](../docs/SCRIPT_MAP.md)  
**DAG truth:** [`config/study_manifest.yaml`](../config/study_manifest.yaml)  
**Button:** `python3 platform/cibuild.py`

If you are learning the project, **do not read this folder top-to-bottom**.  
Read **CORE** only, then SUPPORT when you need ODA/seals.

---

## Tiers (how to read this folder)

| Tier | Meaning | Learn? |
|---|---|---|
| **CORE_DAG** | Invoked by `study_manifest.yaml` during a full run | Yes |
| **CORE_SUPPORT** | Required to *run* CORE (orchestrator, ODA, verify helpers) | When running |
| **REPORT** | Regenerates control markdown/CSV — not ADaM science | No (while learning) |
| **LAB / OUT_OF_DAG** | Capability demo or optional tool | Only if needed |
| **TEST** | Unit/integration tests for platform pieces | Devs only |
| **ARCHIVE** | Moved to `tools/archive/` — not live | Never as prod |

---

## CORE_DAG (on the release pipeline)

| Script | Role |
|---|---|
| `check_gate_g00_governance.py` | Product-claim / scope lock |
| `check_gate_g02_specification.py` | SAP / spec lock |
| `gen_adam_labels.R` | ADaM label/order artifacts |
| `check_gate_g07_reviewer_package.py` | Reviewer guides lock |
| `export_datasetjson.py` | Dataset-JSON export (additive layer) |
| `build_ars.py` | ARS export (additive layer) |
| `build_usdm.py` | USDM export (additive layer) |
| `package_ectd.py` | Assemble Module 5 style tree → `08_submission_package/m5/` |
| `build_ectd_backbone.py` | eCTD index / STF |
| `materialize_ectd.py` | Materialize sequence `ectd/0000/` |
| `check_log_cleanliness.py` | Log gate |
| `build_release_run_manifest.py` | Hash seal binding |

Analysis programs live under `04_analysis_datasets/programs/` — not here.  
QC recon scripts live under `06_qc_evidence/reconciliation/`.

---

## CORE_SUPPORT (run / operate, not “extra product”)

| Script | Role |
|---|---|
| `cibuild.py` | Orchestrator — **only entrypoint you need** |
| `manifest.py` | Manifest loader used by cibuild |
| `oda_broker.py` | Resilient SAS OnDemand connection |
| `seed_sdtm.py` | Job A: seed SDTM on ODA |
| `generate_config.py` | YAML → generated SAS config |
| `build_release_candidate_checklist.py` | RC checklist machine grade |
| `verify_evidence.py` | Evidence checks |
| `_oda_render_tfl.py` | **OUT_OF_DAG** SAS figure render (capability; not spine seal proof) |

Release re-check from repo root: `python3 scripts/verify_release.py`

---

## REPORT (ignore while learning biometrics)

These print status into `docs/` or `platform/*/`.  
They do **not** derive ADSL/ADTTE.

| Script | Typical output |
|---|---|
| `build_delivery_controls.py` | Runs a suite of control builders |
| `build_delivery_dashboard.py` | `docs/DELIVERY_EVIDENCE_DASHBOARD.md` |
| `build_orchestrator_gate_map.py` | `docs/ORCHESTRATOR_GATE_MAP.md` |
| `build_tfl_output_index.py` | `docs/TFL_OUTPUT_INDEX.md` |
| `build_metadata_control_report.py` | metadata control report |
| `build_validation_strategy_report.py` | validation strategy report |
| `build_source_profile.py` | source profile |
| `build_ctq_traceability_report.py` | CTQ report |
| `check_delivery_model.py` · `check_evidence_layers.py` · `check_renv_lock.py` | structural checks |

---

## LAB / UTILITY (optional)

| Script | Role |
|---|---|
| `uplift_sdtm_34.R` | SDTM 3.4 uplift (source-side transform path) |
| `adam_conf_check.R` · `adam_conf_parse_define.py` | Local ADaM conformance helpers |
| `validate_core_rules.py` · `run_adam_conformance.sh` · `run_core_conformance.sh` | CORE/local rules |
| `apply_metadata_lineage.py` | Lineage check vs YAML |
| `lint_sas.py` | SAS lint |
| `ct_cross_validation.py` · `date_precision_sensitivity.py` | Sensitivity / CT labs |
| `tte_utils.py` | Shared TTE helpers |

---

## TEST

| Script | Role |
|---|---|
| `test_oda_broker.py` | Broker unit tests |

---

## Generated status piles (not source)

Ignore these when learning:

- `*.json` status files next to builders (`pipeline_health.json` is the seal-facing exception)  
- `platform/*/…_status.json` report side-products  
- `__pycache__/`  

Sealed snapshot of a genuine ODA run: `platform/evidence/`

---

## How to run (minimal)

```bash
# Full spine
python3 platform/cibuild.py              # sim if no SAS
python3 platform/cibuild.py --real-sas   # genuine ODA/local when available

# Package only (after data exist)
python3 platform/package_ectd.py

# Seals re-check
python3 scripts/verify_release.py

# Control-report suite only (not biometrics)
python3 platform/build_delivery_controls.py
```

---

## Cleanup / git surface policy

| Action | Where |
|---|---|
| What is allowed in git | [`docs/REPO_SURFACE_POLICY.md`](../docs/REPO_SURFACE_POLICY.md) |
| Dead / one-off code | `tools/archive/` **local only** (gitignored) |
| Orphan disposition | `06_qc_evidence/audit/orphans_dangling_deadcode.csv` |
| Human spine | `docs/SCRIPT_MAP.md` |
| Interviewer walk | `docs/INTERVIEWER_GUIDE.md` |

**Tracked here:** orchestrator source + **seal allowlist JSON** + `evidence/`.  
**Not tracked:** regenerable `*_status.json` piles, inventory CSVs, control-report side products.

Do **not** add new scripts to this folder without assigning a tier in this README and either:

1. wiring them in `study_manifest.yaml`, or  
2. labeling them REPORT / LAB / OUT_OF_DAG explicitly.
