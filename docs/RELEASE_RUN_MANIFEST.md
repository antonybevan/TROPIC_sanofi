# TROPIC Release-Run Manifest

Generated: 2026-08-01 17:15:58 UTC

> Hash-sealed run manifest for current artifacts. This is not an electronic signature or Part 11 attestation.

## Verdict

- Status: `PASS`
- Evidence grade: `release_candidate`
- Manifest SHA-256 seal: `8958d3e6a54b17a36eda439f90d48c2c01f437fd1f52f194f073b3d339ec7d1c`
- SAS execution mode: `oda`
- Pipeline health: `GREEN`
- Run scope: `full_dag` (34 recorded / 33 release-required upstream stages)
- Git HEAD: `d0e6d52be3b5ab2d4e4a1e0a25249ae8a46ec7b9`
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
| ADSL | 3f8d04330bf632eaedecd6d36ee9d738 | c9415de03a58a66cbe4e796fde704f7d | yes | yes | yes |
| ADEX | d67cf536d003915f54637aab08a51392 | a210d7116e85cb2f5281f7110866d666 | yes | yes | yes |
| ADCM | 5c4025f64c3d6a66cb72668c13c891a3 | 6fa36b399f0be122d344a839981ef72e | yes | yes | yes |
| ADAE | 67d3e069365f9617304fbc607e58837b | 6224eb053d79716665e17ad20ac0724a | yes | yes | yes |
| ADLB | b4b11664b9fd021f641709eb835ab788 | fe9a449bfc6d97bece359b2280f6b528 | yes | yes | yes |
| ADRS | b69d82aef21d7383640e8aae05307720 | 7d894993ab4b4e305b2691a351bbbf05 | yes | yes | yes |
| ADTTE | 270a5f71c5e9e2772cd3f395cdf5aad2 | a4e7bbafb687528c1828d35a40ea2037 | yes | yes | yes |
| CLINSITE | e41b947dc2baed622c1b5661867c9e92 | d25ded1533baf1f47de317ae9428a46d | yes | yes | yes |

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
