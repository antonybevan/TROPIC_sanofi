# TROPIC Release-Run Manifest

Generated: 2026-08-10 05:30:04 UTC

> Hash-sealed run manifest for current artifacts. This is not an electronic signature or Part 11 attestation.

## Verdict

- Status: `REMEDIATION`
- Evidence grade: `remediation_partial_or_dirty`
- Manifest SHA-256 seal: `9743a5d3610dcba638d454941227363d58011ec2fff46eb9c7bb8f5ad623f095`
- SAS execution mode: `oda`
- Pipeline health: `GREEN`
- Run scope: `full_dag` (37 recorded / 36 release-required upstream stages)
- Git HEAD: `48f4a356967144afe07a33ae38b30d1c6b5d4374`
- Worktree dirty: `True`
- SAS companion figures: `in_dag_real_sas_companion`; current with health=`True`

## Status meanings

- `PASS` — full current DAG + clean worktree + current-run binding; release-candidate grade.
- `REMEDIATION` — hard QC/package bindings hold, but run is partial, dirty, or carries stale companion artifacts; development/remediation evidence only.
- `FAIL` — package/data/QC binding integrity failed.

## Problems

No release-run binding problems detected.

## Remediation reasons (block release-candidate PASS)

- git worktree is dirty (13 porcelain entries); release-candidate lock requires a clean committed state

## Dataset Binding

| Dataset | Prod MD5 | Validation MD5 | Distinct | Package match | Sequence match |
| --- | --- | --- | --- | --- | --- |
| ADSL | 9bdeb452b5a69e848703b2b72d65cc2e | af449fbf7aae6bfd3d138027c643ce31 | yes | yes | yes |
| ADEX | 428834593b14d73b0ac60e60f29c31c4 | 13911c79ed1325df40f638381bbd592e | yes | yes | yes |
| ADCM | e0e9354f7a8a9c9fbd719a6e3816283d | f6a3b5c8d012a8ae016b94f47761b4a1 | yes | yes | yes |
| ADAE | 2fe5407c1d46b93da91a36279a1b2cf3 | 5df69444b278dfd800f4a62599b57e08 | yes | yes | yes |
| ADLB | 2b9c3e3990caad9c4792b78a09731652 | aa5851a6401778b66ba7987e8c42e8a2 | yes | yes | yes |
| ADRS | 5a474e7669dad1e67edf7f84db5322a1 | 32eaf12c32738c23d2ae65b5972594f9 | yes | yes | yes |
| ADTTE | 3c6b3a6f84fb52f690e8da12565d17a4 | 4bd67f905701a21d073b62a72024f937 | yes | yes | yes |
| CLINSITE | ce6fb6da51061d32f9fec531cd614800 | c8e3ba6f0b1e5b80a5a3076c9807bde1 | yes | yes | yes |

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
