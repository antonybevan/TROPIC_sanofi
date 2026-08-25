# TROPIC Release-Run Manifest

Generated: 2026-08-24 18:28:15 UTC

> Hash-sealed run manifest for current artifacts. This is not an electronic signature or Part 11 attestation.

## Verdict

- Status: `FAIL`
- Evidence grade: `failed_binding`
- Manifest SHA-256 seal: `5cfe39b98f1a440fcb977e7b179e284157800eaa1280d3c80f584e2c4d8c6950`
- SAS execution mode: `sim`
- Pipeline health: `RED`
- Run scope: `partial_dag` (18 recorded / 40 release-required upstream stages)
- Git HEAD: `149c30e87dc863299b7b4fda9e12e713c44cf872`
- Worktree dirty: `False`
- SAS companion figures: `in_dag_real_sas_companion`; current with health=`False`

## Status meanings

- `PASS` — full current DAG + clean worktree + current-run binding; release-candidate grade.
- `REMEDIATION` — hard QC/package bindings hold, but run is partial, dirty, or carries stale companion artifacts; development/remediation evidence only.
- `FAIL` — package/data/QC binding integrity failed.

## Problems

- pipeline_health.json source_tree_sha256 does not match the current control/program tree
- pipeline_health.json is not GREEN
- live run is not bound to a real SAS execution mode
- pipeline provenance_guard did not pass
- dataset reconciliation is not non-simulated PASS
- F-042 pain-response SAS/R reconciliation is not PASS

## Remediation reasons (block release-candidate PASS)

- pipeline_health does not cover a full current DAG run (18 recorded in health / 40 release-required upstream stages; missing=22; not_run=0). Acceptable as targeted remediation evidence only.
- stages missing from pipeline_health: Admiral ADSL Re-derivation, Admiral ADTTE Re-derivation (OS/PFS), Admiral Core Reconciliation, Synthetic Comparator Bridge Parity, Efficacy & Safety TFL Suite Compilation, Numerical Results Reconciliation (SAS vs R), Forest-HR Reconciliation (SAS vs R), Figure-Data Reconciliation (SAS vs R) (+14 more)

## Dataset Binding

| Dataset | Prod MD5 | Validation MD5 | Distinct | Package match | Sequence match |
| --- | --- | --- | --- | --- | --- |
| ADSL | 2d7c30c54714bc9af95b4ab810d285cb | 084fbddaf6b33b9ffcb57232a66a98c8 | yes | yes | yes |
| ADEX | 46a39e314378ecffeb44f290a863c1c2 | 51bd316d0e27a8563a14f3aed009f90e | yes | yes | yes |
| ADCM | fc7624930da53933b5a3e97957ef6c4e | e291610307bd51a4bef0f82b55e60e3b | yes | yes | yes |
| ADAE | b836cfc476a99d7e2367d490b19f18bb | 8ba83bb6c716855b3c1e284e78a52141 | yes | yes | yes |
| ADLB | 16a188164d337019e5c54f317d044500 | 68111bdc87808abf978d0b39ac1c2f3b | yes | yes | yes |
| ADRS | d7a1d5eb0fabe388ba99b8a791f6e831 | 06b2ad3a858726cded92fb56dc9d286c | yes | yes | yes |
| ADTTE | c78db9eec2b31e3dedf62ae78805dc99 | cf782a1207b00292391a00c8b3b2cf1f | yes | yes | yes |
| CLINSITE | 6344232006265ea3cc3dd59cabd1558a | 68ebfa684a269b39fcc4659174337a2d | yes | yes | yes |

## QC Verdicts

| Check | Status | Source |
| --- | --- | --- |
| pipeline_health | RED | platform/pipeline_health.json |
| reconciliation | FAIL | platform/reconciliation_status.json |
| results_reconciliation | PASS | platform/results_reconciliation_status.json |
| forest_reconciliation | PASS | platform/forest_reconciliation_status.json |
| figure_data_reconciliation | PASS | platform/figure_data_reconciliation_status.json |
| cbzp_bridge | PASS | platform/cbzp_bridge_status.json |
| spec_define | PASS | platform/conformance/spec_define_conformance.json |
| spec_data | PASS | platform/conformance/spec_data_conformance.json |
| metadata_control | pass | platform/metadata_control/metadata_control_status.json |
| log_cleanliness | PASS | platform/log_cleanliness/log_cleanliness_status.json |
| tfl_output_index | pass | platform/tfl_output_index_status.json |
| validation_strategy | PASS | platform/validation_strategy/validation_strategy_status.json |
| simulation_operating_characteristics | PASS | platform/simulation_operating_characteristics/simulation_oc_status.json |
| regulatory_baseline | PASS | 06_qc_evidence/gates/regulatory_baseline_status.json |

## Machine-Readable Outputs

- `platform/release_run_manifest/release_run_manifest.json`
- `platform/release_run_manifest/release_run_files.csv`
- `06_qc_evidence/audit/output_hash_binding.csv`
