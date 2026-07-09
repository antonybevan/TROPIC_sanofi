# TROPIC Orchestrator Gate Map

Generated: 2026-07-09 14:50:46 UTC

> Maps the actual `study_manifest.yaml` pipeline stages to the professional delivery gates in `delivery_workstreams.yaml`. This report shows what the runtime DAG controls directly and which delivery gates remain document/control-report governed.

## Summary

| Item | Value |
| --- | --- |
| Status | warning |
| Manifest stages | 30 |
| Mapped stages | 30 |
| Unmapped stages | 0 |
| Delivery gates | 10 |
| Stage-covered gates | G01, G03, G04, G05, G06, G08, G09 |
| Not currently stage-gated | G00, G02, G07 |

## Stage-to-Gate Map

| Stage | Name | Script | Runner | Parallel | Manifest gated | Delivery gates | Rationale |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | ADaM Spec Label/Order Artifacts | 06_telemetry/gen_adam_labels.R | rscript | no | no | G03,G06 | spec-derived metadata export contract |
| 2 | Real SDTM Staging Ingest | 03_validation_r/v_staging_ingest.R | logrx | no | no | G01 | source intake/staging |
| 3 | R SDTM Validation | 03_validation_r/v_sdtm_validation.R | logrx | no | no | G01,G06 | source structural validation |
| 4 | R ADSL Validation | 03_validation_r/v_adsl_validation.R | logrx | no | no | G04,G06 | ADaM validation track |
| 5 | R ADEX Validation | 03_validation_r/v_adex_validation.R | logrx | yes | no | G04,G06 | ADaM validation track |
| 6 | R ADCM Validation | 03_validation_r/v_adcm_validation.R | logrx | yes | no | G04,G06 | ADaM validation track |
| 7 | R ADAE Validation | 03_validation_r/v_adae_io_validation.R | logrx | yes | no | G04,G06 | ADaM validation track |
| 8 | R ADLB Validation | 03_validation_r/v_adlb_validation.R | logrx | yes | no | G04,G06 | ADaM validation track |
| 9 | R ADRS Validation | 03_validation_r/v_adrs_validation.R | logrx | yes | no | G04,G06 | ADaM validation track |
| 10 | R ADTTE Validation | 03_validation_r/v_adtte_validation.R | logrx | no | no | G04,G06 | ADaM validation track |
| 11 | R BIMO Validation | 03_validation_r/v_bimo_validation.R | logrx | no | no | G04,G06 | BIMO validation track |
| 12 | SAS Production (ODA/Real/Simulated) | SIMULATE sentinel / SAS production resolver | sas_mode | no | no | G04 | production analysis dataset build |
| 13 | Cross-Language Audit Reconcile | 05_reconciliation/cross_lang_audit.R | logrx | no | yes | G04,G06 | dataset-level reconciliation gate |
| 14 | Admiral ADSL Re-derivation | 03_validation_r/admiral_adsl.R | rscript | no | no | G04,G06 | third-engine T1 ADSL re-derivation (admiral) |
| 15 | Admiral ADTTE Re-derivation (OS/PFS) | 03_validation_r/admiral_adtte.R | rscript | no | no | G04,G06 | third-engine T1 OS/PFS re-derivation (admiral) |
| 16 | Admiral Core Reconciliation | 05_reconciliation/admiral_reconcile.R | rscript | no | yes | G04,G06 | third-engine scoped core reconciliation gate |
| 17 | Synthetic Comparator Bridge Parity | 01_raw_source/check_cbzp_bridge.R | rscript | no | no | G05,G06 | synthetic comparator bridge control before TFLs |
| 18 | Efficacy & Safety TFL Suite Compilation | 09_tfl/tfl_generation.R | rscript | no | yes | G05 | TFL output generation gate |
| 19 | Numerical Results Reconciliation (SAS vs R) | 05_reconciliation/results_reconcile.R | logrx | no | yes | G06 | results-level reconciliation gate |
| 20 | Forest-HR Reconciliation (SAS vs R) | 05_reconciliation/forest_reconcile.R | rscript | no | no | G06 | figure-driving statistic reconciliation |
| 21 | ADaM Spec to Define Conformance | 07_define_xml/check_define_conformance.R | rscript | no | no | G03,G06 | metadata spec-to-define conformance |
| 22 | ADaM Spec to Data Conformance | 03_validation_r/spec_data_checks.R | rscript | no | no | G03,G04,G06 | metadata spec-to-data conformance |
| 23 | Dataset-JSON Export (v1.1) | 06_telemetry/export_datasetjson.py | python | no | no | G04,G08 | dataset exchange layer |
| 24 | Analysis Results Standard (ARS v1.0) | 06_telemetry/build_ars.py | python | no | no | G05,G08 | analysis results metadata/export layer |
| 25 | USDM Study Definition (v3.0) | 06_telemetry/build_usdm.py | python | no | no | G03,G08 | study definition metadata/export layer |
| 26 | eCTD Final Package | 06_telemetry/package_ectd.py | python | no | no | G08 | Module 5 package assembly |
| 27 | eCTD Backbone + STF (sequence 0000) | 06_telemetry/build_ectd_backbone.py | python | no | no | G08 | eCTD backbone and STF assembly |
| 28 | Materialize eCTD Sequence | 06_telemetry/materialize_ectd.py | python | no | no | G08,G09 | sequence materialization and checksum verification |
| 29 | Log Cleanliness Gate | 06_telemetry/check_log_cleanliness.py | python | no | no | G06,G09 | execution-log scan for unapproved warnings/errors and reviewed exception caps |
| 30 | Release Run Manifest Binding | 06_telemetry/build_release_run_manifest.py | python | no | no | G09 | current run hash binding and QC verdict seal |

## Gate Coverage

| Gate | Name | Layer | Runtime stage coverage |
| --- | --- | --- | --- |
| G00 | governance_scope_lock | specification | not currently stage-gated |
| G01 | source_intake_lock | source_data | Real SDTM Staging Ingest, R SDTM Validation |
| G02 | analysis_specification_lock | specification | not currently stage-gated |
| G03 | metadata_lock | metadata | ADaM Spec Label/Order Artifacts, ADaM Spec to Define Conformance, ADaM Spec to Data Conformance, USDM Study Definition (v3.0) |
| G04 | analysis_dataset_promotion | analysis_dataset | R ADSL Validation, R ADEX Validation, R ADCM Validation, R ADAE Validation, R ADLB Validation, R ADRS Validation, R ADTTE Validation, R BIMO Validation, SAS Production (ODA/Real/Simulated), Cross-Language Audit Reconcile, Admiral ADSL Re-derivation, Admiral ADTTE Re-derivation (OS/PFS), Admiral Core Reconciliation, ADaM Spec to Data Conformance, Dataset-JSON Export (v1.1) |
| G05 | output_promotion | output | Synthetic Comparator Bridge Parity, Efficacy & Safety TFL Suite Compilation, Analysis Results Standard (ARS v1.0) |
| G06 | qc_signoff | qc_evidence | ADaM Spec Label/Order Artifacts, R SDTM Validation, R ADSL Validation, R ADEX Validation, R ADCM Validation, R ADAE Validation, R ADLB Validation, R ADRS Validation, R ADTTE Validation, R BIMO Validation, Cross-Language Audit Reconcile, Admiral ADSL Re-derivation, Admiral ADTTE Re-derivation (OS/PFS), Admiral Core Reconciliation, Synthetic Comparator Bridge Parity, Numerical Results Reconciliation (SAS vs R), Forest-HR Reconciliation (SAS vs R), ADaM Spec to Define Conformance, ADaM Spec to Data Conformance, Log Cleanliness Gate |
| G07 | reviewer_package_lock | reviewer_explanation | not currently stage-gated |
| G08 | submission_package_materialization | submission_package | Dataset-JSON Export (v1.1), Analysis Results Standard (ARS v1.0), USDM Study Definition (v3.0), eCTD Final Package, eCTD Backbone + STF (sequence 0000), Materialize eCTD Sequence |
| G09 | release_candidate_lock | qc_evidence | Materialize eCTD Sequence, Log Cleanliness Gate, Release Run Manifest Binding |

## Interpretation

- `Manifest gated` means `cibuild.py` has name-keyed post-stage gate logic or the stage exits non-zero on failure.
- `Delivery gates` are the professional operating-model gates the stage supports.
- `Not currently stage-gated` means the gate is controlled by documentation or generated evidence reports today, not by a first-class runtime DAG stage.

## Machine-Readable Outputs

- `06_telemetry/orchestrator_gate_map/orchestrator_gate_map_status.json`
- `06_telemetry/orchestrator_gate_map/orchestrator_gate_map.csv`
