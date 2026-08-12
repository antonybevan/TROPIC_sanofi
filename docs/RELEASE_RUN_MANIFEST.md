# TROPIC Release-Run Manifest

Generated: 2026-08-12 10:43:48 UTC

> Hash-sealed run manifest for current artifacts. This is not an electronic signature or Part 11 attestation.

## Verdict

- Status: `PASS`
- Evidence grade: `release_candidate`
- Manifest SHA-256 seal: `d02a7f0f869fa61a0aa3a4e79e22c3d09cf75fd00f27bbbffd73588c9346ba03`
- SAS execution mode: `oda`
- Pipeline health: `GREEN`
- Run scope: `full_dag` (37 recorded / 36 release-required upstream stages)
- Git HEAD: `cbf6a14a581facb974c2496fcd09267b64c3de23`
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
| ADSL | 4ed95a1b98c18ba2f6f45cbef2832f4f | 11cbb9ce0a28717cc85fe18fe25bd7c1 | yes | yes | yes |
| ADEX | 19e77f8c0404e24985367e8a9b12cae6 | 9fcf09fee23d4a213a646f8fa12d2c03 | yes | yes | yes |
| ADCM | 405cf0291f382e0f8f6feba685d04edc | f4208aeac57dac410cadc3df53c56961 | yes | yes | yes |
| ADAE | de4fbb341f002a9ea016173342c1634b | cb4cc20bed60d456269e42266abf4603 | yes | yes | yes |
| ADLB | e1cc58e2a6cecb45cafbd69fb4e53d77 | 3cc14032497b30c2d46aeac2d1a34e88 | yes | yes | yes |
| ADRS | 2499d595f1b21a828fcb9885d7b19535 | 52ef9d97b18345d27c7bf3a113572d3c | yes | yes | yes |
| ADTTE | 91412ee2309930aff89814c959f3a41a | 4ab58004322aef0c9a14ee5e1dadbd5f | yes | yes | yes |
| CLINSITE | a6feae0d4b1d18a84c833479493025b3 | 1ffc083af386d50a46d9eb43d172b73a | yes | yes | yes |

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
| regulatory_baseline | PASS | 06_qc_evidence/gates/regulatory_baseline_status.json |

## Machine-Readable Outputs

- `platform/release_run_manifest/release_run_manifest.json`
- `platform/release_run_manifest/release_run_files.csv`
- `06_qc_evidence/audit/output_hash_binding.csv`
