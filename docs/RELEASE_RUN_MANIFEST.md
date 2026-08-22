# TROPIC Release-Run Manifest

Generated: 2026-08-22 15:19:05 UTC

> Hash-sealed run manifest for current artifacts. This is not an electronic signature or Part 11 attestation.

## Verdict

- Status: `PASS`
- Evidence grade: `release_candidate`
- Manifest SHA-256 seal: `8ffa14fdaa3e67d74882e576162c382574ce7b19901acc585a226297fabe6421`
- SAS execution mode: `oda`
- Pipeline health: `GREEN`
- Run scope: `full_dag` (40 recorded / 39 release-required upstream stages)
- Git HEAD: `1371d9c9c9be0a50bdf02c60ffdc72615520a7fe`
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
| ADSL | bf45bd9b872cbd7bda5074da236e2049 | 3d9593a132a791b9adb4d7d8dd2ddbef | yes | yes | yes |
| ADEX | 46efb3a4b69d9b7a8f27c4385124f8ad | c137f8dc1b204e420795e075eedd78f4 | yes | yes | yes |
| ADCM | fdaafe05a1095b0faf7e5603b067d4f1 | 7392a2ef5c22de1c409abbb8482e9dd5 | yes | yes | yes |
| ADAE | 4b0b5881a281fc474887327569894fe6 | f29e57748a3d565285b2b06fce812ffe | yes | yes | yes |
| ADLB | 0d52a21346cf5007bf4f47d01e6218f1 | 1909743f5695e61ac83b68ff6e55b258 | yes | yes | yes |
| ADRS | 9bf00f9d6fea7bacde81db7d1b41b775 | b446d77efcd86c071433a8ef13ba0e14 | yes | yes | yes |
| ADTTE | d24f63d6ba92a49ecef392867f269550 | 5c50541f567e2f87bf7ab1434ad9c75d | yes | yes | yes |
| CLINSITE | 4bb2c8b02a3c7d295fcafccac33ac105 | 634dff0fdc2a2c641f4e0e4cc1b1aa45 | yes | yes | yes |

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
