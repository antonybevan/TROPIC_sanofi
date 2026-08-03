# TROPIC Release-Run Manifest

Generated: 2026-08-03 06:57:48 UTC

> Hash-sealed run manifest for current artifacts. This is not an electronic signature or Part 11 attestation.

## Verdict

- Status: `REMEDIATION`
- Evidence grade: `remediation_partial_or_dirty`
- Manifest SHA-256 seal: `06ab0deeb40307780421390e6871be8cd685e627f6efe95924f34e1d468fa4d9`
- SAS execution mode: `oda`
- Pipeline health: `GREEN`
- Run scope: `full_dag` (34 recorded / 33 release-required upstream stages)
- Git HEAD: `427cad3f2dc7c8dfe909d40dc3cf1edbc3bc7ffe`
- Worktree dirty: `True`
- SAS companion figures: `in_dag_real_sas_companion`; current with health=`True`

## Status meanings

- `PASS` — full current DAG + clean worktree + current-run binding; release-candidate grade.
- `REMEDIATION` — hard QC/package bindings hold, but run is partial, dirty, or carries stale companion artifacts; development/remediation evidence only.
- `FAIL` — package/data/QC binding integrity failed.

## Problems

No release-run binding problems detected.

## Remediation reasons (block release-candidate PASS)

- git worktree is dirty (38 porcelain entries); release-candidate lock requires a clean committed state

## Dataset Binding

| Dataset | Prod MD5 | Validation MD5 | Distinct | Package match | Sequence match |
| --- | --- | --- | --- | --- | --- |
| ADSL | ac6ebde4b31d4e8c7f022c38822f556f | 6b32a7a346a8e97471178164eb5a6d02 | yes | yes | yes |
| ADEX | 5a2e1b52e7f610a1d0aa1290cf6c4cbb | b87d28ace68ade43f277419de4e3a1e9 | yes | yes | yes |
| ADCM | a745b733b5e9ffe1b732e26cca59b5c8 | 27335e6e9700014a5cc4604c170e4950 | yes | yes | yes |
| ADAE | 265220b56d6901ba9c6e71abdf6632fb | 3f5d592b2733701f3016a604062108c2 | yes | yes | yes |
| ADLB | a6225ef901d1f097bb0172572ee6fa43 | 199b1afc009ba7184a006549d9fd03d5 | yes | yes | yes |
| ADRS | 20a05f7ece68299aae72716b34ac7aeb | e02de0c3a3581f719ac4a24820b3de50 | yes | yes | yes |
| ADTTE | 3747adb8ee453f0fd290cb31a2a41fd5 | 15f6e5ba95bff11f1a51f04083de12f7 | yes | yes | yes |
| CLINSITE | be9a7973767139376dc630dfaf10b9db | 343aa1e3d960f9242d2f4e89858697b6 | yes | yes | yes |

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
