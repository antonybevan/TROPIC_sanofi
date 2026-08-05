# TROPIC — Live-SAS Isolated Rerun Audit (2026-08-05)

**Date:** 2026-08-05
**Scope:** Independent reproducibility audit of the sealed release (main @ `e260ad4`,
v0.2.0 portfolio release; release-run manifest seal `cd8b0d8f6db48cc7f4908532489052b25c6628dbfffab1d5e13cfa5b96a138cb`)
via a **real-SAS (ODA) rerun in an isolated clean worktree**.
**Product claim:** Path A — controlled non-submission clinical biometrics programming
demonstration (study EFC6193 / XRP6258). Not an FDA filing, not Part 11, not a
re-analysis of trial efficacy.
**Auditor:** Antony Bevan (single-author limitation acknowledged). Session executed via
Codex CLI; completed and recorded via Hermes agent on 2026-08-05.

## Purpose

Independently verify that the released build reproduces: same source/control tree, same
locked R environment, genuine ODA SAS execution, and that the committed gates, tests,
and release seals remain internally consistent. Recorded without modifying any released
seal: the committed release evidence (2026-08-04, GREEN) is untouched.

## Method

- Isolated clean git worktree: `/private/tmp/tropic-release-audit-e260`, HEAD
  `e260ad439232ca63af4ddeec8cfdb8b8c1c043ac` (detached at the released commit).
- Source/control tree digest recorded by the rerun (`fe78f9d639935acdffdb1501134806cd98011f1fa9fbcff2fb2658c5350792ba`)
  **equals** the digest computed from the released main tree (verified independently).
- R environment: `renv.lock` sha256 `a9ba2082ce1f227add5d2cb400fb70688ea5031fef238dcf1bf1928de2700630`
  **equals** the released lockfile (verified independently); R 4.6.0.
- SAS: genuine ODA execution via SASPy 5.107.1 (OpenJDK 26.0.1), endpoint
  `odaws01-apse1-2.oda.sas.com`, SAS `9.04.01M8P022223`, 1 attempt, preflight OK
  (all required checks, `authinfo` mode 0600), probe nonce echoed, results downloaded.
- Attempt 1 (05:20:15Z): aborted at Admiral ADSL re-derivation — the temporary worktree
  lacked the local `admiral` R package; the runner rolled back its generated outputs.
  Environmental, not an analysis or pipeline defect.
- Attempt 2 (05:30:34Z): completed the 27-stage DAG with the released locked R library
  attached.

## Results (attempt 2, 05:30:34Z)

| Stage | Result |
|---|---|
| Governance Scope Lock (G00), Analysis Specification Lock (G02), ADaM Spec Label/Order Artifacts | PASS |
| Real SDTM Staging Ingest; R validations (SDTM, ADSL, ADEX, ADCM, ADAE, ADLB, ADRS, ADTTE, BIMO) | PASS (10/10) |
| SAS Production (ODA/Real) | PASS |
| Cross-Language Audit Reconcile | PASS — real SAS vs R, all 8 domains; `F042_PAIN_RESPONSE` endpoint control PASS |
| Admiral ADSL + ADTTE (OS/PFS) re-derivation, Core Reconciliation | PASS — 0 cell differences, n=371 |
| Synthetic Comparator Bridge Parity | PASS |
| Efficacy & Safety TFL Suite Compilation | PASS |
| Numerical Results, Forest-HR, Figure-Data Reconciliation (SAS vs R) | PASS (3/3) |
| ADaM Spec to Define / to Data Conformance | PASS (2/2) |
| Reviewer Package Lock (G07) | PASS |
| **Dataset-JSON Export (v1.1)** | **FAIL** |
| ARS v1.0, USDM v3.0, eCTD Final Package, eCTD Backbone+STF, Materialize eCTD, Log Cleanliness Gate, Release Run Manifest Binding (stages 28–34) | NOT RUN — DAG aborts on first stage FAIL |

Pipeline status: **RED** — driven solely by the Dataset-JSON stage. All 26 executed
stages before it passed.

## Dataset-JSON failure — root cause and disposition

`platform/export_datasetjson.py` reads SDTM XPTs from
`08_submission_package/m5/datasets/tropic/tabulations/sdtm/datasets/`, a **gitignored
generated path** (`.gitignore:29` → `08_submission_package/m5/**/*.xpt`). A clean
checkout does not contain those XPTs, so the exporter **fails closed by design**
("ERROR: no SDTM XPT inputs … refuse empty Dataset-JSON export"). The ADaM side
exported successfully (8/8 domains) because the DAG regenerates ADaM `*_prod.xpt`
in-tree.

- **Not a regression of the released build:** the released build (2026-08-04, GREEN)
  contains the generated XPTs in its material tree; the committed `pipeline_health.json`
  records 34/34 stages PASS.
- **Consistent with accepted finding F-020** (Dataset-JSON lifecycle): documented
  fail-closed-on-zero-inputs behavior; exploratory exchange layer not consumed by
  `package_ectd.py`; residual accepted.
- **Disposition: ACCEPTED** as an environmental boundary of isolated clean-checkout
  reruns. No code change in this audit. Optional future hardening (not authorized here):
  skip gracefully when m5 SDTM inputs are absent, or bind the generated XPT set into the
  release-run manifest so a clean-tree full-DAG rerun can reproduce this stage.

## Coverage scope note

The rerun executed the data/TFL/QC core (stages 1–27). Because the DAG aborts on the
Dataset-JSON FAIL, the packaging tail (stages 28–34: ARS, USDM, eCTD package/backbone/
materialize, log-cleanliness gate, release-manifest binding) was **not re-executed** in
the isolated rerun; its committed release evidence (2026-08-04) is unchanged and is
re-verified below.

## Independent verification (no ODA rerun, released main tree)

| Check | Result |
|---|---|
| `python3 scripts/verify_release.py` (clean released tree) | **31/31 PASS**, exit 0 |
| `python3 -m pytest -q` | **96 passed** |
| Release-candidate status (committed) | **18/18 PASS**, `live_sas_execution_mode=oda`, generated 2026-08-04 17:56Z |
| Release-run manifest seal | intact — all `release_manifest.*` checks PASS |
| R package consistency | `renv.lock` sha256 equals the rerun-recorded hash |
| Source/control tree consistency | digest equals between released tree and rerun |

## Honesty

A GREEN committed seal plus a passing `verify_release.py` re-check proves the committed
seals are internally consistent — it does not prove ODA is reachable today. This record
exists because a genuine ODA session **was** exercised on 2026-08-05 (probe nonce
echoed, results downloaded, SAS logs captured as evidence). The rerun's RED status is an
environmental artifact of the isolated clean tree (Dataset-JSON inputs absent), not a
release defect.

## Evidence

Committed under `06_qc_evidence/audit/run_records/2026-08-05-live-sas-isolated-rerun/`:
`pipeline_health.json`, `pipeline_health_log.jsonl`, `health_dashboard.md`,
`reconciliation_status.json`, `admiral_reconciliation_status.json`,
`results_reconciliation_status.json`, `forest_reconciliation_status.json`,
`figure_data_reconciliation_status.json`, `cbzp_bridge_status.json`, `oda_status.json`,
`stage_cache.json`.

The raw ODA SAS session logs (`oda_master_driver.log`, `oda_tfl.log`, 2026-08-05) are
retained as local copies in the same directory and in the audit worktree
(`/private/tmp/tropic-release-audit-e260/04_analysis_datasets/programs/sas/`) but are
**excluded from git per the repo's `*.log` policy** (`.gitignore:73`); the log-derived
evidence (`pipeline_health.json`, `pipeline_health_log.jsonl`, `oda_status.json`) is
committed in their place.

## Exit

Live-SAS isolated rerun audit **closed**: the released build reproduced on the
data/TFL/QC core with genuine ODA SAS under the identical locked R environment and
source tree; the single stage failure is an accepted environmental boundary (F-020);
released seals re-verified 31/31 plus 96/96 tests. The temporary audit worktree remains
in place for reference; it is safe to delete once the branch is merged.
