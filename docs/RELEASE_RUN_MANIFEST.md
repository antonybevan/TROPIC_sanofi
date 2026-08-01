# TROPIC Release-Run Manifest

Generated: 2026-08-01 17:37:33 UTC

> Hash-sealed run manifest for current artifacts. This is not an electronic signature or Part 11 attestation.

## Verdict

- Status: `PASS`
- Evidence grade: `release_candidate`
- Manifest SHA-256 seal: `6da30dcdca370f31c13b5d2c2d82c430856a209fd340d5228bdbd7aac0d7277a`
- SAS execution mode: `oda`
- Pipeline health: `GREEN`
- Run scope: `full_dag` (34 recorded / 33 release-required upstream stages)
- Git HEAD: `e01d7518fc511341a670d9f56d5efafb67e8f48d`
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
| ADSL | 76c26416925be9445611763271ee02b5 | 96a00b9718212997eb43c7de25e6908d | yes | yes | yes |
| ADEX | 23bb0fa47085034e62deda876b274d50 | 0c06386461d93490f464c84ce0c86afe | yes | yes | yes |
| ADCM | 54a19b94465b69d652b75985e2d3370b | f30af8aba0042ce454559dc225fa10e8 | yes | yes | yes |
| ADAE | 49e97858f09c0aa027c88ca7e4b589f5 | 6cd380f713f8ad60b5307dcd2aad8a85 | yes | yes | yes |
| ADLB | 76fb79a28b597312e783904ce8f409fb | 36c026b0acb3c206525247b242d64d66 | yes | yes | yes |
| ADRS | 2f3207708e4b4cb2675d404d5e8c9245 | 16d1cabc944352f8b13df1af61852dfb | yes | yes | yes |
| ADTTE | ad4c253d384bea8c3a5a13d102ca6938 | 5c99f1cea83e9ddb39c34a9259e07823 | yes | yes | yes |
| CLINSITE | a17b6acfbef1f4fe37f103aeeb5343b8 | 1742837b04efc99b658b410c6c869d37 | yes | yes | yes |

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
