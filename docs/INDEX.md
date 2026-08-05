# TROPIC Documentation Index

**Purpose:** Stop dump-scrolling. Three tours — open only what your role needs.  
**Binding claim:** [`PRODUCT_CLAIM.md`](PRODUCT_CLAIM.md) (Path A · controlled non-submission demo)  
**Presentation model:** [`SUBMISSION_REPO_PRESENTATION_RESEARCH.md`](SUBMISSION_REPO_PRESENTATION_RESEARCH.md)

---

## 30-second start (everyone)

| Order | Document | Role |
|---:|---|---|
| 1 | [`INTERVIEWER_GUIDE.md`](INTERVIEWER_GUIDE.md) | What we want them to see |
| 2 | [`PRODUCT_CLAIM.md`](PRODUCT_CLAIM.md) | What we may assert |
| 3 | [`REPO_SURFACE_POLICY.md`](REPO_SURFACE_POLICY.md) | What is / isn’t in git |
| 4 | [`../08_submission_package/README.md`](../08_submission_package/README.md) | Review package tour |
| 5 | [`RELEASE_NOTE_v0.2.2-portfolio.md`](RELEASE_NOTE_v0.2.2-portfolio.md) | Current portfolio seal narrative |
| 6 | [`SCRIPT_MAP.md`](SCRIPT_MAP.md) | What runs vs ignore |
| 7 | `python3 scripts/verify_release.py` | Machine re-check |

---

## Tour A — Reviewer / mock FDA / portfolio interviewer

**Goal:** Understand the study package without factory noise.  
**Time box:** 15–30 minutes.

| Step | Open | What you get |
|---:|---|---|
| 1 | [`PRODUCT_CLAIM.md`](PRODUCT_CLAIM.md) | Path A boundary |
| 2 | [`../08_submission_package/m5/datasets/tropic/`](../08_submission_package/m5/datasets/tropic/) | SDTM / ADaM / BIMO co-location |
| 3 | [`../07_reviewer_explanation/guides/ADRG.md`](../07_reviewer_explanation/guides/ADRG.md) | Analysis data narrative |
| 4 | [`../07_reviewer_explanation/guides/SDRG.md`](../07_reviewer_explanation/guides/SDRG.md) | Tabulation narrative |
| 5 | [`../07_reviewer_explanation/guides/BDRG.md`](../07_reviewer_explanation/guides/BDRG.md) | BIMO narrative |
| 6 | TFL appendices under `08_submission_package/m5/53-clin-stud-rep/…/tropic/` | Figures + tables |
| 7 | [`RELEASE_NOTE_v0.2.2-portfolio.md`](RELEASE_NOTE_v0.2.2-portfolio.md) | What “PASS” means under Path A |
| 8 | [`workstreams/WS5_KNOWN_DIFFERENCES_MEMO.md`](workstreams/WS5_KNOWN_DIFFERENCES_MEMO.md) | Residual honesty |

**Do not start with:** `platform/` JSON dumps, regenerated `*_REPORT.md` files, or `config/` YAML.

**Say in interview:**  
“Review surface is Module 5 style under `08_submission_package/m5/`. Guides explain; seals bound the demo; claim freezes scope.”

---

## Tour B — Engineer / statistical programmer / platform

**Goal:** See how the factory is controlled and how programs produce the package.  
**Time box:** 30–60 minutes.

### B1 — Control plane

| Open | Why |
|---|---|
| [`SCRIPT_MAP.md`](SCRIPT_MAP.md) | CORE scripts only — reverse-engineer order |
| [`../config/study_manifest.yaml`](../config/study_manifest.yaml) | DAG truth (stages) |
| [`../config/study_config.yaml`](../config/study_config.yaml) | Study parameters |
| [`../config/tfl_output_catalog.yaml`](../config/tfl_output_catalog.yaml) | Controlled vs deferred TFLs |
| [`../config/validation_strategy.yaml`](../config/validation_strategy.yaml) | Risk-based validation allocation |
| [`../config/evidence_layers.yaml`](../config/evidence_layers.yaml) | Physical evidence-layer contract |
| [`../config/delivery_workstreams.yaml`](../config/delivery_workstreams.yaml) | Workstream structure |

### B2 — Execution entrypoints

| Open | Why |
|---|---|
| [`../platform/README.md`](../platform/README.md) | Factory tiers (what to ignore) |
| [`../platform/cibuild.py`](../platform/cibuild.py) | Orchestrator |
| [`../tools/archive/README.md`](../tools/archive/README.md) | Dead/one-off code (not spine) |
| [`../platform/package_ectd.py`](../platform/package_ectd.py) | Module 5 packager |
| [`../scripts/verify_release.py`](../scripts/verify_release.py) | Seal re-check |
| [`runbooks/ODA_GUIDE.md`](runbooks/ODA_GUIDE.md) | Real SAS / ODA operator path |
| [`runbooks/OFFLINE_LAYER_RUNBOOK.md`](runbooks/OFFLINE_LAYER_RUNBOOK.md) | Dataset-JSON / ARS / USDM offline |

### B3 — Analysis programs & specs

| Open | Why |
|---|---|
| `02_specifications/sap/TROPIC_SAP_v4.0_industry_grade.docx` | Programming authority |
| `04_analysis_datasets/programs/sas/` | Production track |
| `04_analysis_datasets/programs/r/` | Validation + TFL track |
| `03_metadata/adam/ADaM_spec.xlsx` | Metadata control source |
| `03_metadata/define/` | Define-XML + validation tools |
| [`PIPELINE_ARCHITECTURE_REDESIGN.md`](PIPELINE_ARCHITECTURE_REDESIGN.md) | Evidence-chain architecture |
| [`BIOMETRICS_DELIVERY_OPERATING_MODEL.md`](BIOMETRICS_DELIVERY_OPERATING_MODEL.md) | Department operating model |
| [`ORCHESTRATOR_GATE_MAP.md`](ORCHESTRATOR_GATE_MAP.md) | Stage ↔ gate mapping |

### B4 — Multi-study / tests

| Open | Why |
|---|---|
| [`../studies/README.md`](../studies/README.md) | DEMO02 engine proof |
| `tests/` | R smoke and figure contracts |

**Say in interview:**  
“Factory is manifest-driven. Programs under `04_…/programs/`. Package is a *product* of the DAG, not a hand-maintained second truth.”

---

## Tour C — QC / validation / findings disposition

**Goal:** Challenge the package; see residual risk and seal honesty.  
**Time box:** 30–45 minutes.

| Step | Open | Why |
|---:|---|---|
| 1 | [`PRODUCT_CLAIM.md`](PRODUCT_CLAIM.md) | Claim before evidence |
| 2 | [`../06_qc_evidence/reconciliation/`](../06_qc_evidence/reconciliation/) | SAS↔R · admiral · figure · forest |
| 3 | [`../06_qc_evidence/reconciliation/ADMIRAL_RECONCILIATION.md`](../06_qc_evidence/reconciliation/ADMIRAL_RECONCILIATION.md) | Third-engine core |
| 4 | [`../06_qc_evidence/gates/`](../06_qc_evidence/gates/) | G00 / G02 / G07 status |
| 5 | [`../06_qc_evidence/audit/FINDINGS_DISPOSITION_BOARD.md`](../06_qc_evidence/audit/FINDINGS_DISPOSITION_BOARD.md) | Crit/Major disposition |
| 6 | [`../06_qc_evidence/audit/findings_register.csv`](../06_qc_evidence/audit/findings_register.csv) | Machine register |
| 7 | [`workstreams/WS5_KNOWN_DIFFERENCES_MEMO.md`](workstreams/WS5_KNOWN_DIFFERENCES_MEMO.md) | Known residual differences |
| 8 | [`RELEASE_CANDIDATE_CHECKLIST.md`](RELEASE_CANDIDATE_CHECKLIST.md) | RC go/no-go human view |
| 9 | [`RELEASE_RUN_MANIFEST.md`](RELEASE_RUN_MANIFEST.md) | Hash seal human view |
| 10 | `platform/pipeline_health.json` | Live run telemetry (`sas_execution_mode`, scope) |
| 11 | [`../platform/evidence/`](../platform/evidence/) | Frozen genuine ODA snapshot |

**Validation strategy control:**  
[`VALIDATION_STRATEGY_CONTROL_REPORT.md`](VALIDATION_STRATEGY_CONTROL_REPORT.md) · [`../config/validation_strategy.yaml`](../config/validation_strategy.yaml)

**Say in interview:**  
“QC is a warehouse with disposition, not a pile of green badges. Findings are RESOLVED or ACCEPTED with reason before release narrative.”

---

## Workstream packs (operating departments)

| Pack | Path |
|---|---|
| Execution board | [`WORKSTREAM_EXECUTION_BOARD.md`](WORKSTREAM_EXECUTION_BOARD.md) |
| WS packs | [`workstreams/`](workstreams/) |
| Endpoint decision pack | [`workstreams/decisions/ENDPOINT_DECISION_RECORD_F042_T11_8_2026-08-03.md`](workstreams/decisions/ENDPOINT_DECISION_RECORD_F042_T11_8_2026-08-03.md) |
| Delivery model | [`BIOMETRICS_DELIVERY_OPERATING_MODEL.md`](BIOMETRICS_DELIVERY_OPERATING_MODEL.md) |
| Regulatory workflow research | [`REGULATORY_WORKFLOW_RESEARCH.md`](REGULATORY_WORKFLOW_RESEARCH.md) |

---

## Generated control reports (local only — not in git)

These are **build/control outputs**. They are **gitignored** under the portfolio surface policy.  
Regenerate locally when needed; do **not** present them as peers of ADRG.

```bash
python3 platform/build_delivery_controls.py
```

Typical local outputs (not portfolio face):

- `docs/DELIVERY_EVIDENCE_DASHBOARD.md`
- `docs/ORCHESTRATOR_GATE_MAP.md`
- `docs/TFL_OUTPUT_INDEX.md`
- `docs/*_REPORT.md` control printers
- Most `platform/**/*_status.json` outside the [seal allowlist](REPO_SURFACE_POLICY.md)

**Tracked seal narratives (human):**

| Doc | Path |
|---|---|
| Release-run manifest (human) | [`RELEASE_RUN_MANIFEST.md`](RELEASE_RUN_MANIFEST.md) |
| Release-candidate checklist | [`RELEASE_CANDIDATE_CHECKLIST.md`](RELEASE_CANDIDATE_CHECKLIST.md) |

---

## Architecture & research (deep dives)

| Doc | When to read |
|---|---|
| [`PIPELINE_ARCHITECTURE_REDESIGN.md`](PIPELINE_ARCHITECTURE_REDESIGN.md) | Evidence-chain redesign & migration map |
| [`SUBMISSION_REPO_PRESENTATION_RESEARCH.md`](SUBMISSION_REPO_PRESENTATION_RESEARCH.md) | Why dual surface; noise diagnosis |
| [`REGULATORY_WORKFLOW_RESEARCH.md`](REGULATORY_WORKFLOW_RESEARCH.md) | Industry workflow grounding |
| [`I_J_generalisation_plan.md`](I_J_generalisation_plan.md) | Multi-study generalisation notes |

---

## Document hierarchy (conflict resolution)

```text
1. PRODUCT_CLAIM.md          ← what we may assert
2. SAP v4.0 + lock memo      ← analysis programming authority
3. config/* catalogs         ← controlled scope (TFL, validation, layers)
4. Machine seals             ← whether this run of controlled scope is green
5. ADRG / SDRG / BDRG        ← explanation (must not exceed 1–4)
6. Generated reports         ← status views only
```

If a generated dashboard contradicts PRODUCT_CLAIM, the dashboard is wrong or stale — fix the claim process, do not “talk past” the claim.
