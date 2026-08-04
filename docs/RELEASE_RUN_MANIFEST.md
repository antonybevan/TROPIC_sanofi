# TROPIC Release-Run Manifest

Generated: 2026-08-04 08:02:41 UTC

> Hash-sealed run manifest for current artifacts. This is not an electronic signature or Part 11 attestation.

## Verdict

- Status: `PASS`
- Evidence grade: `release_candidate`
- Manifest SHA-256 seal: `101cbb0e093dc398bf79c0ad6c082c5657f24bdd768057ca94846cfb600803f9`
- SAS execution mode: `oda`
- Pipeline health: `GREEN`
- Run scope: `full_dag` (34 recorded / 33 release-required upstream stages)
- Git HEAD: `fefa0dafc7c0a9942b348009012e0358f61c781d`
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
| ADSL | aa1c14106c18a035508a2017aac8c7c3 | 8ba5426cceb360fe324e91962cc88049 | yes | yes | yes |
| ADEX | 588c239dcd0b65882d424663b9416f9b | c0220ff8dc00a8c248d963088a2c581c | yes | yes | yes |
| ADCM | 717044d977f9f8247fbb14cc597369d6 | 8e630562fc9cec5425ca6582f9ff7499 | yes | yes | yes |
| ADAE | d711f15a2dde8e022dab69cf3b2fba94 | 988e65aac5a84973ace2ad8bf2cbc645 | yes | yes | yes |
| ADLB | 7bbeeffef16a5b412e7b9919dbccd1bd | 9cdc557fa40b77bf1747958a4a4a6504 | yes | yes | yes |
| ADRS | cec53e45337ca281497fb8901ab31e0c | f570ace96270c5300104eb27224198b4 | yes | yes | yes |
| ADTTE | d513c014f1c6c1934607a6551cc3c5fe | 75ef7044a87300cd615f1c2e58cc46cd | yes | yes | yes |
| CLINSITE | 52433f594e18bb606674488801485e1b | 8b289a62a302698160d4f380ae11e804 | yes | yes | yes |

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
