# TROPIC Release-Run Manifest

Generated: 2026-08-10 05:16:55 UTC

> Hash-sealed run manifest for current artifacts. This is not an electronic signature or Part 11 attestation.

## Verdict

- Status: `PASS`
- Evidence grade: `release_candidate`
- Manifest SHA-256 seal: `48c4ca2183a8f555557332a0a632bf7d56311d61295d0f17c81e4c443b9039dd`
- SAS execution mode: `oda`
- Pipeline health: `GREEN`
- Run scope: `full_dag` (37 recorded / 36 release-required upstream stages)
- Git HEAD: `caf5fc1e9ca2bbc16ea8ebdbaad61ecdb8a63a43`
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
| ADSL | 6a8b121877fcc2eadcbd7a791c94914c | 0d6a5c8b5d3961c493689cec204a932b | yes | yes | yes |
| ADEX | 8d4464035b8a405add3f4763da8c015c | a17ea8f28e17bd5bef20c71518ca3742 | yes | yes | yes |
| ADCM | 34fc070d50545c3c28d15d37cae50a71 | aa6ed5a26ef7c301f0ba60d906a75d33 | yes | yes | yes |
| ADAE | 12de6360fd860d576e70c2e4e17858e8 | 8c6ce6e3853ee6641518bf92a486b330 | yes | yes | yes |
| ADLB | d4bcced6222bdba679cb4378a8363d07 | f77d08c3017e6b7cc9b32f5c2224f955 | yes | yes | yes |
| ADRS | 18ed3eee4e0f6f017391bc24a4acade8 | 0f91f891b3a0515b6a9c5b30294c1d05 | yes | yes | yes |
| ADTTE | 9af8c16a4c03be482064370439f5b2c4 | 3d4621381c7b33db880ccc7239cc33a7 | yes | yes | yes |
| CLINSITE | 81e4812e1f3cd49c54bbfea957e90c79 | b97c89d8dcf1f8d1f9e7736fd9dd7c26 | yes | yes | yes |

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
