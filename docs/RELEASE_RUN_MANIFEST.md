# TROPIC Release-Run Manifest

Generated: 2026-08-12 05:54:34 UTC

> Hash-sealed run manifest for current artifacts. This is not an electronic signature or Part 11 attestation.

## Verdict

- Status: `PASS`
- Evidence grade: `release_candidate`
- Manifest SHA-256 seal: `719c58421ff921402d92b1a5b7fd0e071b9cad55d022598693d3d69f38697ead`
- SAS execution mode: `oda`
- Pipeline health: `GREEN`
- Run scope: `full_dag` (37 recorded / 36 release-required upstream stages)
- Git HEAD: `59905d33fa1dd19340808f7f7398869fbee92dcd`
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
| ADSL | f281078bdbe258bd25236439f7df8865 | ac133c48bb3fb7f9c1e34ac63cc0e95e | yes | yes | yes |
| ADEX | 14b14ae4a4d9215403e913ef5d13a084 | 23ba5f19f871baf0d9e8ce9f3d2c44e5 | yes | yes | yes |
| ADCM | 416de24b8944846d8eec3b68e3d7c33f | 91e54074588d51587cc14b939e1abf4c | yes | yes | yes |
| ADAE | ebc8aa81945cf36b14fd530772af4791 | 997ab72f3557a1d8534439ba9e614bdd | yes | yes | yes |
| ADLB | a376c78f99d970c8831c9b757a6a1438 | 6b5080705b476db3ee19fc8c09ce1f95 | yes | yes | yes |
| ADRS | 8ed69641d53fb72016568d374549e659 | f67a0dfb47a3a513d5b5fcfe767cf72f | yes | yes | yes |
| ADTTE | 1dc688418ec3d9d224879944344ac951 | cb8b70b406dd1e8fbf1c16e5c03c8286 | yes | yes | yes |
| CLINSITE | 0ef46d9143fc2154dbbf36089e55828e | fe5a8cc1a1a43a5db4acf9b60512723e | yes | yes | yes |

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
