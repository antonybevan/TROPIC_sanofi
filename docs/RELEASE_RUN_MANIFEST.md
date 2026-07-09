# TROPIC Release-Run Manifest

Generated: 2026-07-09 15:17:41 UTC

> Hash-sealed run manifest for current artifacts. This is not an electronic signature or Part 11 attestation.

## Verdict

- Status: `PASS`
- Evidence grade: `release_candidate`
- Manifest SHA-256 seal: `c01e744fe5ba3a1e70fbe4a0b4304da1a8f211edb21cc5ba76f85db3f6ed0201`
- SAS execution mode: `oda`
- Pipeline health: `GREEN`
- Run scope: `full_dag` (30 recorded / 29 release-required upstream stages)
- Git HEAD: `29d801653fb5ca941a938daa7e23c3a184299c74`
- Worktree dirty: `False`
- SAS companion figures: `out_of_dag_capability_demo`; current with health=`False`

## Status meanings

- `PASS` — full current DAG + clean worktree + current-run binding; release-candidate grade.
- `REMEDIATION` — hard QC/package bindings hold, but run is partial, dirty, or carries out-of-DAG stale companions; development/remediation evidence only.
- `FAIL` — package/data/QC binding integrity failed.

## Problems

No release-run binding problems detected.

## Dataset Binding

| Dataset | Prod MD5 | Validation MD5 | Distinct | Package match | Sequence match |
| --- | --- | --- | --- | --- | --- |
| ADSL | d9cfee91cdb096cc2e43ae99c8ad619e | 5155f1e456965a4256a7369cc216609c | yes | yes | yes |
| ADEX | 717cdca2457f3eba7ccd06a38a7577fb | a6c76c2c59c2ab6af231e2e500251e34 | yes | yes | yes |
| ADCM | 5c0702cd4c2f1c671e6640698a7485e9 | b4f988f19ca095907e38764d412aa365 | yes | yes | yes |
| ADAE | 904f2e110c5c09a8cff597ed666a4b55 | 818ac945013f34c41e5e80b2a7d9bb0a | yes | yes | yes |
| ADLB | 24046922705d1158a832560509e125b5 | 0b519760c3eddd61c9f7ac115b24aa73 | yes | yes | yes |
| ADRS | 59946e567f7e1d6c6fb7732607c407c4 | c04e5bc6223afa222d8bd3efc1f522bf | yes | yes | yes |
| ADTTE | 2dbf1810c71cc23ae315bb36735cf2c1 | d10422f3d2f6f8fd9cf5d2c414ff1171 | yes | yes | yes |
| CLINSITE | ef3bc205ba75ba6c6ee4000150c36d6c | 9254afe8677543b4435bb2aee8af1df5 | yes | yes | yes |

## QC Verdicts

| Check | Status | Source |
| --- | --- | --- |
| pipeline_health | GREEN | 06_telemetry/pipeline_health.json |
| reconciliation | PASS | 06_telemetry/reconciliation_status.json |
| results_reconciliation | PASS | 06_telemetry/results_reconciliation_status.json |
| forest_reconciliation | PASS | 06_telemetry/forest_reconciliation_status.json |
| cbzp_bridge | PASS | 06_telemetry/cbzp_bridge_status.json |
| spec_define | PASS | 06_telemetry/conformance/spec_define_conformance.json |
| spec_data | PASS | 06_telemetry/conformance/spec_data_conformance.json |
| metadata_control | pass | 06_telemetry/metadata_control/metadata_control_status.json |
| log_cleanliness | PASS | 06_telemetry/log_cleanliness/log_cleanliness_status.json |
| tfl_output_index | pass | 06_telemetry/tfl_output_index_status.json |
| validation_strategy | PASS | 06_telemetry/validation_strategy/validation_strategy_status.json |

## Machine-Readable Outputs

- `06_telemetry/release_run_manifest/release_run_manifest.json`
- `06_telemetry/release_run_manifest/release_run_files.csv`
- `audit/output_hash_binding.csv`
