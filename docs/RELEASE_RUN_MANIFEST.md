# TROPIC Release-Run Manifest

Generated: 2026-08-05 13:38:48 UTC

> Hash-sealed run manifest for current artifacts. This is not an electronic signature or Part 11 attestation.

## Verdict

- Status: `PASS`
- Evidence grade: `release_candidate`
- Manifest SHA-256 seal: `03e61e26b73281fa9f2343fa4be2bda1ca024d3a92487fadc98d327cb116a78b`
- SAS execution mode: `oda`
- Pipeline health: `GREEN`
- Run scope: `full_dag` (34 recorded / 33 release-required upstream stages)
- Git HEAD: `6d5742adabe5a7e0860ad9c092cabb4cbdaedc66`
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
| ADSL | 7b377eeaca0df74137f5c90344322222 | 5861d7d910e7a9d5c709d503e7cf580d | yes | yes | yes |
| ADEX | b5e7d260fa156d83db35572969ae27da | 242781c69a93282a2c519b14ea34f42d | yes | yes | yes |
| ADCM | 6661643b41b4b4f459ba074b08d0f0d9 | 2e886869e4c3221626cc9b5e08bb8b9d | yes | yes | yes |
| ADAE | 3b802a8d60c1af45ab4856b3e5e55563 | f6949aecccba8ec86fef6ba8d40342f2 | yes | yes | yes |
| ADLB | 59e20c9d97af131fdc5154f8a5775eba | f1d1d7baddb62f082a66d6dc49a4a586 | yes | yes | yes |
| ADRS | 4805b8bc44653faaffbba43a21259036 | c97d1d7ffe36be693041baf7ab70da29 | yes | yes | yes |
| ADTTE | e18470a2e8c69ae54a4868c3010b0336 | 66a8893625ae27cd4ce3fe0e7646e1a6 | yes | yes | yes |
| CLINSITE | c399213d187448acb1a823981a5a7432 | 85854edc8bbbffe54a35029966133f1e | yes | yes | yes |

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
