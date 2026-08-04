# TROPIC Release-Run Manifest

Generated: 2026-08-04 06:56:10 UTC

> Hash-sealed run manifest for current artifacts. This is not an electronic signature or Part 11 attestation.

## Verdict

- Status: `REMEDIATION`
- Evidence grade: `remediation_partial_or_dirty`
- Manifest SHA-256 seal: `70367f1729f0529374baa728eb30dfd9aeadbf5dd4a299c5eded5ac68f4c343e`
- SAS execution mode: `oda`
- Pipeline health: `GREEN`
- Run scope: `full_dag` (34 recorded / 33 release-required upstream stages)
- Git HEAD: `e967d692bbc2b99db7d69ff3947c576768db3f3b`
- Worktree dirty: `True`
- SAS companion figures: `in_dag_real_sas_companion`; current with health=`True`

## Status meanings

- `PASS` — full current DAG + clean worktree + current-run binding; release-candidate grade.
- `REMEDIATION` — hard QC/package bindings hold, but run is partial, dirty, or carries stale companion artifacts; development/remediation evidence only.
- `FAIL` — package/data/QC binding integrity failed.

## Problems

No release-run binding problems detected.

## Remediation reasons (block release-candidate PASS)

- git worktree is dirty (65 porcelain entries); release-candidate lock requires a clean committed state

## Dataset Binding

| Dataset | Prod MD5 | Validation MD5 | Distinct | Package match | Sequence match |
| --- | --- | --- | --- | --- | --- |
| ADSL | 0c727f76e709e443c3dffd0dacaf368f | 7d53c12fb804c3132d546540e702b622 | yes | yes | yes |
| ADEX | 66e548dec7fadd49813e17b00e22f61b | 8cf153662673d1e9100ed9e48f39eca5 | yes | yes | yes |
| ADCM | dc6c55cbce84e3a7c385fcd67cb0dfc8 | 6f395c6aa3d8e8aa7bf901d3568ab223 | yes | yes | yes |
| ADAE | 5cabaecceae3550e75d8b605727d8047 | 26c46397a06c6a4b26f24331aa877b5c | yes | yes | yes |
| ADLB | a9948ef808d08db3ec8ff8798b511336 | 8f24847a59d5baa1964d6dd6af763c9e | yes | yes | yes |
| ADRS | 0f4f634e37f741090a6e0d9ce989cbf2 | b30c7fcb18f6f7982487db56a0aa8e70 | yes | yes | yes |
| ADTTE | bda24363becc1f71cc62d52de86620dd | 47b8fc9d3b2f51ab9d2ca1f7b5740d80 | yes | yes | yes |
| CLINSITE | 5c4743f268f1d3c931c1e27286ad7d45 | e243fdc9a38ec154a6f14eafa825f61b | yes | yes | yes |

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
