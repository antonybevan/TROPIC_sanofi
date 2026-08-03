# TROPIC Release-Run Manifest

Generated: 2026-08-03 07:06:22 UTC

> Hash-sealed run manifest for current artifacts. This is not an electronic signature or Part 11 attestation.

## Verdict

- Status: `PASS`
- Evidence grade: `release_candidate`
- Manifest SHA-256 seal: `f93fd1e94d87e0a70b61045c2b2142f8638e450d459a1704d61eea3e09e54ba4`
- SAS execution mode: `oda`
- Pipeline health: `GREEN`
- Run scope: `full_dag` (34 recorded / 33 release-required upstream stages)
- Git HEAD: `901693c85780ca884f021484fb38cca4bf4f0958`
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
| ADSL | 2f4187938595649721574a78584e0c29 | e0a2d0d0e4e1cd2f1ac7ea97d1076d43 | yes | yes | yes |
| ADEX | 9a9bf3f0231fa6b934d14f112244ff1f | 527013c69ba4a7415d960083dc2d2ce3 | yes | yes | yes |
| ADCM | b2b8c758d5d6ac69fbc978783f5d06aa | 6cfb55c290f474c09d20b2de74eecec9 | yes | yes | yes |
| ADAE | a130b797c25ae9eb542e5f513417b3e0 | 51b852a9630d570b78b4df32e53d4a3f | yes | yes | yes |
| ADLB | 202410222495ee8cfd8f655208b3f1b7 | ed3ea5483ef74c5ae245b76583b52127 | yes | yes | yes |
| ADRS | 098f133552dd4d60d3fa8e8899537c8f | 7533d4799975948956e1587b0798408f | yes | yes | yes |
| ADTTE | b3fcf1f37a4a86a27f8729e188f9cf2d | dd81f12f18b444ae2c5c70bf5272241b | yes | yes | yes |
| CLINSITE | cbaf5748b618c8644b2ebfe91a8be9a6 | 75cc69d461a0cbb440c38c7b6fbcf257 | yes | yes | yes |

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
