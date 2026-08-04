# TROPIC Release-Run Manifest

Generated: 2026-08-04 17:51:26 UTC

> Hash-sealed run manifest for current artifacts. This is not an electronic signature or Part 11 attestation.

## Verdict

- Status: `REMEDIATION`
- Evidence grade: `remediation_partial_or_dirty`
- Manifest SHA-256 seal: `650cdee004dca5bb39dce719325ada6214abf8a7b36026e44227001cd32de4b3`
- SAS execution mode: `oda`
- Pipeline health: `GREEN`
- Run scope: `full_dag` (34 recorded / 33 release-required upstream stages)
- Git HEAD: `77f6b5a4b859a4d7ee4e1b30829333012353e7e0`
- Worktree dirty: `True`
- SAS companion figures: `in_dag_real_sas_companion`; current with health=`True`

## Status meanings

- `PASS` — full current DAG + clean worktree + current-run binding; release-candidate grade.
- `REMEDIATION` — hard QC/package bindings hold, but run is partial, dirty, or carries stale companion artifacts; development/remediation evidence only.
- `FAIL` — package/data/QC binding integrity failed.

## Problems

No release-run binding problems detected.

## Remediation reasons (block release-candidate PASS)

- git worktree is dirty (43 porcelain entries); release-candidate lock requires a clean committed state

## Dataset Binding

| Dataset | Prod MD5 | Validation MD5 | Distinct | Package match | Sequence match |
| --- | --- | --- | --- | --- | --- |
| ADSL | 7b68e93b09c5ba5cbed911ff71c34d61 | 6680ebf77f9bda438d41c6fada98060a | yes | yes | yes |
| ADEX | 3937dc929f98eba707b7a3c56e20b957 | 1c64b7388603da159d48f9a801409e08 | yes | yes | yes |
| ADCM | 208406d2a084fb50b3b725c4b781e29f | 4e053f4dd106240a5992736ecf5df1c4 | yes | yes | yes |
| ADAE | 0fcf81d30f703865c720d4d40d2177c7 | ae252d8dbae0046e2f8d9ee9e22928cd | yes | yes | yes |
| ADLB | fdef20964ff00c24d39aa1e6c3b60cd3 | 9aacf93ebf3d623160a1a1400baf243e | yes | yes | yes |
| ADRS | 1ebb4096b669d54b44187dec93396b5d | b9bed0e3531a4fdfaeb5acd589d618ef | yes | yes | yes |
| ADTTE | 97eac491d283520be593567775234871 | 4f25fcbdb7661fe9e05b0ae42bdde2d8 | yes | yes | yes |
| CLINSITE | eba467aebc9b50e270e8174661dd4a22 | d1e830e766bdda4dce271e40c21d1167 | yes | yes | yes |

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
| tfl_output_index | fail | platform/tfl_output_index_status.json |
| validation_strategy | PASS | platform/validation_strategy/validation_strategy_status.json |

## Machine-Readable Outputs

- `platform/release_run_manifest/release_run_manifest.json`
- `platform/release_run_manifest/release_run_files.csv`
- `06_qc_evidence/audit/output_hash_binding.csv`
