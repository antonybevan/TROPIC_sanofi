# TROPIC Release-Run Manifest

Generated: 2026-08-04 16:34:16 UTC

> Hash-sealed run manifest for current artifacts. This is not an electronic signature or Part 11 attestation.

## Verdict

- Status: `PASS`
- Evidence grade: `release_candidate`
- Manifest SHA-256 seal: `a6f078ae0e49ecfb77fd3189ff3a1b17c20a5b1eea5ae3578d030cf5924b8593`
- SAS execution mode: `oda`
- Pipeline health: `GREEN`
- Run scope: `full_dag` (34 recorded / 33 release-required upstream stages)
- Git HEAD: `d0020b4da2ec951b58ccefc2b4c7968fe1d8eb6e`
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
| ADSL | d12e4528c3ba8bf7dbbc9ffa98e65654 | 1c3fd98f40e2823bdc01905d2b796b43 | yes | yes | yes |
| ADEX | 0ffe22691909add72fd691201adf250d | 851a37836b053695f89ff485dd5bceaa | yes | yes | yes |
| ADCM | 2609a53cab59cee80b6e7f71cd8e3831 | 64c38b6cbd1e4bb1ed764043628bc918 | yes | yes | yes |
| ADAE | 58c1220f64c530c00b6c160da8eeb82f | 2f4911bc34490feb1cf9f66be2dfe56c | yes | yes | yes |
| ADLB | d1975a7d8b0266c3dffaf660f98b40b1 | 9cfab8ed40994d0089d85c7b703ef341 | yes | yes | yes |
| ADRS | b9a9f3dfca176343d9a33546313389a0 | cc8199636a12ee31217e10540ca2b311 | yes | yes | yes |
| ADTTE | 11999a2a046c75ab6d4094e631b12e64 | 753919e8fe649e9c2c32628b73f1a586 | yes | yes | yes |
| CLINSITE | f6f584af76d9da584865632921f98e07 | 5c35fa1a6dcb6cf540ecbbebef26171f | yes | yes | yes |

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
