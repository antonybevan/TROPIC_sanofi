# TROPIC Release-Run Manifest

Generated: 2026-08-01 13:56:32 UTC

> Hash-sealed run manifest for current artifacts. This is not an electronic signature or Part 11 attestation.

## Verdict

- Status: `REMEDIATION`
- Evidence grade: `remediation_partial_or_dirty`
- Manifest SHA-256 seal: `5941b3c04ea6b448337ea00a523db1050a71da66d91090e187b4cf150365c1d4`
- SAS execution mode: `oda`
- Pipeline health: `GREEN`
- Run scope: `full_dag` (34 recorded / 33 release-required upstream stages)
- Git HEAD: `352ad4bfffe4752eac895301df326e3fc684f4a7`
- Worktree dirty: `True`
- SAS companion figures: `out_of_dag_capability_demo`; current with health=`False`

## Status meanings

- `PASS` — full current DAG + clean worktree + current-run binding; release-candidate grade.
- `REMEDIATION` — hard QC/package bindings hold, but run is partial, dirty, or carries out-of-DAG stale companions; development/remediation evidence only.
- `FAIL` — package/data/QC binding integrity failed.

## Problems

No release-run binding problems detected.

## Remediation reasons (block release-candidate PASS)

- git worktree is dirty (64 porcelain entries); release-candidate lock requires a clean committed state

## Dataset Binding

| Dataset | Prod MD5 | Validation MD5 | Distinct | Package match | Sequence match |
| --- | --- | --- | --- | --- | --- |
| ADSL | 162f46d486152028b37e1a66658ba690 | 956f620c6ff1d84bcf283c9ccdb56b49 | yes | yes | yes |
| ADEX | 19f61fe789dfd2ccc43a9193cf790f68 | a4cea14e931c3ca9d00a466cd62612dc | yes | yes | yes |
| ADCM | 4e4b35181ab673cb8165e04ad48a45de | 3dddd239adcd388cfd1ca23a892a4e01 | yes | yes | yes |
| ADAE | 4bacd3200d4d37a924d86cfa25028e5f | 303573050e9304b545d07da7c107a4d3 | yes | yes | yes |
| ADLB | a41f51f39b0c4e841f60233c9dd42098 | 5f61fcd64bcec7b48c0b45a5c5114b14 | yes | yes | yes |
| ADRS | 3df8a9b483618f9410732697f6d9d9de | c32796ed9cd786a40ace5277e8c7a00c | yes | yes | yes |
| ADTTE | d5ff04c12ebcdb89e951ed3f35d3cb7c | e8e9f03fe9a6cfc776a0ce141ecebe04 | yes | yes | yes |
| CLINSITE | cb17506829cd0079a6f9d86c31875270 | 3a50e3178cb4dca1f5654f409026cbaf | yes | yes | yes |

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
