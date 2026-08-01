# TROPIC Release-Run Manifest

Generated: 2026-08-01 17:54:46 UTC

> Hash-sealed run manifest for current artifacts. This is not an electronic signature or Part 11 attestation.

## Verdict

- Status: `PASS`
- Evidence grade: `release_candidate`
- Manifest SHA-256 seal: `070232617a258217662d056a7471b28bd3c4e081d612ae509518a76696f67230`
- SAS execution mode: `oda`
- Pipeline health: `GREEN`
- Run scope: `full_dag` (34 recorded / 33 release-required upstream stages)
- Git HEAD: `73d8ca1341a750065307b50632a7c41e63ec0f85`
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
| ADSL | ccaad05ed203c3b742a0d71322468d22 | 99d5ecc6991b7ae1f8c9cdab341f9c56 | yes | yes | yes |
| ADEX | d9113abcb411618134404c9530aaf1e2 | 7ad5ba7367f9f6e8f6ee7a83f50988c8 | yes | yes | yes |
| ADCM | acb57bac9c0100c2d2a8ac0365097145 | c395686d926254d4ed6a4de2982c4922 | yes | yes | yes |
| ADAE | eb9800d4668b4cf4b630f24c6a876a4b | 4dc175f87a2d9b7e89fd3794af1c69bd | yes | yes | yes |
| ADLB | 75886a988b4f401ee47410908327d8e3 | 68503c12e7ae833963fd32bde761af9c | yes | yes | yes |
| ADRS | 75acbba94280f0ed81b6732186af0b0a | b3d1b3443677e118c002d7009d38ee03 | yes | yes | yes |
| ADTTE | 795db0020c693dc259e316275c5e2d7d | 88b6240fd02d32b6fb8bc647a425f18a | yes | yes | yes |
| CLINSITE | dc8b4d109918b6c2a9ca377c45dfe573 | 6e5f2e2f9d47ed1eec87f747cd515d9d | yes | yes | yes |

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
