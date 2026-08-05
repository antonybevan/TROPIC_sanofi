# TROPIC Release-Run Manifest

Generated: 2026-08-05 06:52:52 UTC

> Hash-sealed run manifest for current artifacts. This is not an electronic signature or Part 11 attestation.

## Verdict

- Status: `PASS`
- Evidence grade: `release_candidate`
- Manifest SHA-256 seal: `315ae1c0374dd8c4311870f33bfc31570f2866df7cfd5d05a492536e6c2ddc55`
- SAS execution mode: `oda`
- Pipeline health: `GREEN`
- Run scope: `full_dag` (34 recorded / 33 release-required upstream stages)
- Git HEAD: `db8d915fe4918e7054372592e4f7b4c7a91975ee`
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
| ADSL | 52796189ec3d1305443b12221825bc1f | 7569c366b00ba7dbd06a74196c5db4ae | yes | yes | yes |
| ADEX | 689bee74696703508b63a01c61bd0692 | 5d1f0725eab0ea73dcf26c2b5d885956 | yes | yes | yes |
| ADCM | 9b975aff9b427475be9c34242b7a1c90 | 951c5b8e84195fddad11e8c3068d7f3d | yes | yes | yes |
| ADAE | 675a1ff7235034a51a766f6dc5820ba9 | dc06623f6d3cd93d611ffea531aeee3e | yes | yes | yes |
| ADLB | aeb78f1b3f0bed8d5cc674791adc8c34 | c3326e24dec500470d00804f58788fec | yes | yes | yes |
| ADRS | 90a595f50196b267f84437f968f8d0de | ddaf1082a91de1dcb3d8e745d9db96cf | yes | yes | yes |
| ADTTE | 2bba1343bb77117e9c9bb70fa6822827 | 2b6c0752cf5ef9bd4784d14163cf8d93 | yes | yes | yes |
| CLINSITE | 98f519ce9841cb43ec1d182f20baff6d | 5605c2f36c28fc5d088c7111c1068b47 | yes | yes | yes |

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
