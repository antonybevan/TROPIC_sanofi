# TROPIC Release-Run Manifest

Generated: 2026-08-01 16:52:45 UTC

> Hash-sealed run manifest for current artifacts. This is not an electronic signature or Part 11 attestation.

## Verdict

- Status: `PASS`
- Evidence grade: `release_candidate`
- Manifest SHA-256 seal: `3b4b20b86f1c759bb15750ef8cffe4e36a2371b0f34d8f70c79a2d0d8fba2d74`
- SAS execution mode: `oda`
- Pipeline health: `GREEN`
- Run scope: `full_dag` (34 recorded / 33 release-required upstream stages)
- Git HEAD: `d5e9957cac5b12024938b0cccae9734980ddbe57`
- Worktree dirty: `False`
- SAS companion figures: `in_dag_real_sas_companion`; current with health=`True`

## Status meanings

- `PASS` — full current DAG + clean worktree + current-run binding; release-candidate grade.
- `REMEDIATION` — hard QC/package bindings hold, but run is partial, dirty, or carries stale companion artifacts; development/remediation evidence only.
- `FAIL` — package/data/QC binding integrity failed.

## Problems

No release-run binding problems detected.

## Dataset Binding

| Dataset | Prod MD5 | Validation MD5 | Distinct | Package match | Sequence match |
| --- | --- | --- | --- | --- | --- |
| ADSL | c5020839ba3af401a419fa49f3c9add2 | ce5e547e0b63a6e6ff3279336a8beba8 | yes | yes | yes |
| ADEX | a7d495198e4f69c09c6932452c35dee8 | c780fd6cd66823043b2e3af3aeb6ba12 | yes | yes | yes |
| ADCM | 7c0aeac6a1ee4c4bb264d9961c6dfdbe | 2e5dc2cc0f86eed827c30e0b09d56b65 | yes | yes | yes |
| ADAE | 616e4e311604261fd9daad7d2d7b3329 | af222ad615d227d1fe37367f8c0bdaf1 | yes | yes | yes |
| ADLB | d52d5677128ae6d0b0a54b94061a24c1 | d555b46c8e0bd06b0e78bde0c048da75 | yes | yes | yes |
| ADRS | afb426398f25eee3c04d88e31d11d98f | 0cf7bf9af03b273f4eb1319c4f5d3fd1 | yes | yes | yes |
| ADTTE | 1fb5f973bdb9fe9e47aff89abd93e49b | 86ff5887cf8016abd4df5c867b9f54af | yes | yes | yes |
| CLINSITE | bdb20b6075ad2ed29934741c60e512cb | 27934203809239b84e6a8dd0cef05996 | yes | yes | yes |

## QC Verdicts

| Check | Status | Source |
| --- | --- | --- |
| pipeline_health | GREEN | platform/pipeline_health.json |
| reconciliation | PASS | platform/reconciliation_status.json |
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

## Machine-Readable Outputs

- `platform/release_run_manifest/release_run_manifest.json`
- `platform/release_run_manifest/release_run_files.csv`
- `06_qc_evidence/audit/output_hash_binding.csv`
