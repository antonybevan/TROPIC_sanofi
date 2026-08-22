# TROPIC Release-Run Manifest

Generated: 2026-08-22 14:56:59 UTC

> Hash-sealed run manifest for current artifacts. This is not an electronic signature or Part 11 attestation.

## Verdict

- Status: `PASS`
- Evidence grade: `release_candidate`
- Manifest SHA-256 seal: `ffbf37b2afebed86c3fafe5932994c37c6ffbab93db0a85d79e79a7353cfaa54`
- SAS execution mode: `oda`
- Pipeline health: `GREEN`
- Run scope: `full_dag` (40 recorded / 39 release-required upstream stages)
- Git HEAD: `78621548559b64d5fca64efb7feee9a002c24f0a`
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
| ADSL | 8072ce822a6827324929137236134d42 | 07c1e3d83bd79e46dc8c5668889b48b9 | yes | yes | yes |
| ADEX | c95b3aa6f1dd70b5a352fcfd1e2d46d2 | 997aec389b2df21eefcf10640e288f79 | yes | yes | yes |
| ADCM | 21b2e2c30d5a465530dfa46d27d41a13 | dfbf0696478239b3a083c03f5d746c33 | yes | yes | yes |
| ADAE | 192b13d0803d8e351e04dfc9a4811592 | d2a71d353bd1dc7b6300d4e1a3878fe8 | yes | yes | yes |
| ADLB | 54afdf012d3c192cab62949fd7cfdc4a | f5bcfb2ccde02031257163368539e027 | yes | yes | yes |
| ADRS | c9698bfad3e31833d5c1a3e8daca4a44 | 41f9ea0924a7cc4d5e3922c07675ca7f | yes | yes | yes |
| ADTTE | a1980c3c1fcd8bc6d87c7296766e0fa7 | 6da1a6615413384ddf9011f94d386f14 | yes | yes | yes |
| CLINSITE | 9dfeca7a2b298c49cd9fc4c5fb4b77a5 | 673c49b1564c5040b3110e6abb5ec714 | yes | yes | yes |

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
