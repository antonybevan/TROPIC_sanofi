# TROPIC Release-Run Manifest

Generated: 2026-08-05 05:55:39 UTC

> Hash-sealed run manifest for current artifacts. This is not an electronic signature or Part 11 attestation.

## Verdict

- Status: `REMEDIATION`
- Evidence grade: `remediation_partial_or_dirty`
- Manifest SHA-256 seal: `33bf77733081a9108386744da24c96313fefe9f81d1331f14f1fe958d7db3e94`
- SAS execution mode: `oda`
- Pipeline health: `GREEN`
- Run scope: `full_dag` (34 recorded / 33 release-required upstream stages)
- Git HEAD: `e260ad439232ca63af4ddeec8cfdb8b8c1c043ac`
- Worktree dirty: `True`
- SAS companion figures: `in_dag_real_sas_companion`; current with health=`True`

## Status meanings

- `PASS` — full current DAG + clean worktree + current-run binding; release-candidate grade.
- `REMEDIATION` — hard QC/package bindings hold, but run is partial, dirty, or carries stale companion artifacts; development/remediation evidence only.
- `FAIL` — package/data/QC binding integrity failed.

## Problems

No release-run binding problems detected.

## Remediation reasons (block release-candidate PASS)

- git worktree is dirty (9 porcelain entries); release-candidate lock requires a clean committed state

## Dataset Binding

| Dataset | Prod MD5 | Validation MD5 | Distinct | Package match | Sequence match |
| --- | --- | --- | --- | --- | --- |
| ADSL | 4f6bfe5d4541f056b324f7790ec364f1 | 184fdb1b02100c302667b4072f5338b6 | yes | yes | yes |
| ADEX | fb331cf2055d24c38da183bd8d67ca89 | 447ede5569149d092e192eca6afc5119 | yes | yes | yes |
| ADCM | 1ab6884ab20f24091b17842861ee03f4 | 144cc515c2aa587c567e7d2de34e4fa9 | yes | yes | yes |
| ADAE | 805bdc3192815fdbd589177c16c040a5 | d7b0978722c980609102753f845712fb | yes | yes | yes |
| ADLB | 55124dea1735021ed4cae6b217208fe3 | ccd9e742ba1ed939fd8a6cf1d9d878b3 | yes | yes | yes |
| ADRS | a00593d45faa6c44921ee0c79bab9ee4 | d8840b56079a9c6b49aee506c39297d4 | yes | yes | yes |
| ADTTE | 481b18a9e5f6bf77888016366b991f4f | efc667968eb7df0e866cdf7bf66fc56a | yes | yes | yes |
| CLINSITE | ed7bc6c6216381887a170591dacf2b62 | d772cd135ff47c265b54ec3a9568e17f | yes | yes | yes |

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
