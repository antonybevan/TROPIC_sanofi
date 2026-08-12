# TROPIC Release-Run Manifest

Generated: 2026-08-12 09:30:02 UTC

> Hash-sealed run manifest for current artifacts. This is not an electronic signature or Part 11 attestation.

## Verdict

- Status: `REMEDIATION`
- Evidence grade: `remediation_partial_or_dirty`
- Manifest SHA-256 seal: `67a5e044baeb63b8b8c19726cd2706cfcd552767a29ab53968102a52fefeab1b`
- SAS execution mode: `oda`
- Pipeline health: `GREEN`
- Run scope: `full_dag` (37 recorded / 36 release-required upstream stages)
- Git HEAD: `6ea76682778d23e8c8ff907300b5870df0ec4034`
- Worktree dirty: `True`
- SAS companion figures: `in_dag_real_sas_companion`; current with health=`True`

## Status meanings

- `PASS` — full current DAG + clean worktree + current-run binding; release-candidate grade.
- `REMEDIATION` — hard QC/package bindings hold, but run is partial, dirty, or carries stale companion artifacts; development/remediation evidence only.
- `FAIL` — package/data/QC binding integrity failed.

## Problems

No release-run binding problems detected.

## Remediation reasons (block release-candidate PASS)

- git worktree is dirty (49 porcelain entries); release-candidate lock requires a clean committed state

## Dataset Binding

| Dataset | Prod MD5 | Validation MD5 | Distinct | Package match | Sequence match |
| --- | --- | --- | --- | --- | --- |
| ADSL | 10b956d9b60193635c257369d86a39b1 | 6cd5a2be3da475cf979503bc17ef6a1a | yes | yes | yes |
| ADEX | cc3048543a3d8070aae1b556e13bf621 | 607e6fbf48764f7b45408794584833fb | yes | yes | yes |
| ADCM | e298b072cb65b9b3be1184176d96795a | 30b98dbe55d5bdbba26959f3a06d5423 | yes | yes | yes |
| ADAE | 8379a5182d43fe766f5a824e55b386aa | 255f223bab23db6230ff31a54c044506 | yes | yes | yes |
| ADLB | 604b98ae3909ddcdf19d9c681f9e16d2 | f8485247813e3f8ec21835da0b6f559d | yes | yes | yes |
| ADRS | fb23ec7a911ee56dcde8e8f6c5bfb27e | 1cf30301f36fffaf5c368fee9b8aa06b | yes | yes | yes |
| ADTTE | b1503f8ca82010573c20bf5897ebd9b5 | 8db75c83191188514af410dcfee5cc5e | yes | yes | yes |
| CLINSITE | 10cd6ed9cfd2fbb8ee366b59dc784e96 | 5143d84c8889b2f68683b1dfa51adbb1 | yes | yes | yes |

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
