# TROPIC Release-Run Manifest

Generated: 2026-08-15 01:12:13 UTC

> Hash-sealed run manifest for current artifacts. This is not an electronic signature or Part 11 attestation.

## Verdict

- Status: `FAIL`
- Evidence grade: `failed_binding`
- Manifest SHA-256 seal: `6a214a682d7419a4ae7be7953562f67c69c7951491894ac20326be565dc62f6a`
- SAS execution mode: `oda`
- Pipeline health: `GREEN`
- Run scope: `partial_dag` (37 recorded / 39 release-required upstream stages)
- Git HEAD: `0ee4deff32c0ea758d100928a40cb45a45e2bad4`
- Worktree dirty: `False`
- SAS companion figures: `in_dag_real_sas_companion`; current with health=`True`

## Status meanings

- `PASS` — full current DAG + clean worktree + current-run binding; release-candidate grade.
- `REMEDIATION` — hard QC/package bindings hold, but run is partial, dirty, or carries stale companion artifacts; development/remediation evidence only.
- `FAIL` — package/data/QC binding integrity failed.

## Problems

- pipeline_health.json source_tree_sha256 does not match the current control/program tree
- governance-only seal rebind does not match current source tree

## Remediation reasons (block release-candidate PASS)

- pipeline_health does not cover a full current DAG run (37 recorded in health / 39 release-required upstream stages; missing=3; not_run=0). Acceptable as targeted remediation evidence only.
- stages missing from pipeline_health: Simulation Operating Characteristics, Simulation MAP and Report, Simulation Evidence Independent Verification

## Dataset Binding

| Dataset | Prod MD5 | Validation MD5 | Distinct | Package match | Sequence match |
| --- | --- | --- | --- | --- | --- |
| ADSL | 4ed95a1b98c18ba2f6f45cbef2832f4f | 3d71d58bd32b8694d17cf15a78ea43c7 | yes | yes | yes |
| ADEX | 19e77f8c0404e24985367e8a9b12cae6 | d621a587446386a5590d29cb1d9ad7ce | yes | yes | yes |
| ADCM | 405cf0291f382e0f8f6feba685d04edc | 21a5ed39e46a2b2721b6a6b0a9c3dfd2 | yes | yes | yes |
| ADAE | de4fbb341f002a9ea016173342c1634b | 2966750a603b182c50642cff3337f1f1 | yes | yes | yes |
| ADLB | e1cc58e2a6cecb45cafbd69fb4e53d77 | 62a81d964f1ea3cf7e492c38d2a18d16 | yes | yes | yes |
| ADRS | 2499d595f1b21a828fcb9885d7b19535 | 6b07678ec50eab43c598b450da4c7a44 | yes | yes | yes |
| ADTTE | 91412ee2309930aff89814c959f3a41a | 5ed2bd6946db54a6179f213663c82417 | yes | yes | yes |
| CLINSITE | a6feae0d4b1d18a84c833479493025b3 | 844f666ba4132f41a35886253c4ee7fb | yes | yes | yes |

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
| simulation_operating_characteristics | PASS | platform/simulation_operating_characteristics/simulation_oc_status.json |
| regulatory_baseline | PASS | 06_qc_evidence/gates/regulatory_baseline_status.json |

## Machine-Readable Outputs

- `platform/release_run_manifest/release_run_manifest.json`
- `platform/release_run_manifest/release_run_files.csv`
- `06_qc_evidence/audit/output_hash_binding.csv`
