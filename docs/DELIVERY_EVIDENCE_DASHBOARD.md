# TROPIC Delivery Evidence Dashboard

Generated: 2026-07-09 16:40:39 UTC

> This dashboard is generated from `config/evidence_layers.yaml` and `config/delivery_workstreams.yaml`. It is an architecture and evidence-control view, not a claim that the package is submission-ready.

## Readiness Snapshot

| Check | Status |
| --- | --- |
| Required workstream artifacts | PASS |
| Evidence layers | 8 |
| Delivery workstreams | 9 |
| Handoff gates | 10 |

## Evidence Layers

| Layer | Objective | Required present | Required missing | Other present | Other not present |
| --- | --- | --- | --- | --- | --- |
| source_data | Document controlled source intake, data access limits, source profiling, and source-to-analysis mapping. | 3 | 0 | 5 | 2 |
| specification | Control clinical analysis authority: SAP lock, assumptions, clinical parameters, and derivation rules. | 10 | 0 | 0 | 0 |
| metadata | Provide machine-readable and reviewer-readable dataset metadata, controlled terminology, and traceability. | 10 | 0 | 6 | 0 |
| analysis_dataset | Build and exchange SDTM/ADaM analysis datasets with reproducible program provenance. | 4 | 0 | 3 | 0 |
| output | Generate traceable tables, figures, listings, and analysis-results metadata. | 4 | 0 | 9 | 0 |
| qc_evidence | Capture risk-based validation, reconciliation, conformance, run telemetry, manifests, and audit evidence. | 17 | 0 | 23 | 0 |
| reviewer_explanation | Explain datasets, conformance, assumptions, limitations, outputs, and validation to a reviewer. | 6 | 0 | 1 | 0 |
| submission_package | Materialize an eCTD-style package after data, metadata, outputs, QC, and reviewer explanation gates pass. | 3 | 0 | 3 | 0 |

## Delivery Workstreams

| Workstream | Function | Owns gates | Consumes | Produces |
| --- | --- | --- | --- | --- |
| governance_scope | Governance and scope control | G00, G09 | specification, qc_evidence, reviewer_explanation | specification, reviewer_explanation |
| source_intake | Data access, privacy, and source intake | G01 | source_data | source_data, qc_evidence |
| statistical_specification | Statistical and analysis specification | G02 | source_data, specification | specification, metadata, reviewer_explanation |
| standards_metadata | Standards and metadata governance | G03 | specification | metadata, qc_evidence |
| adam_bimo_programming | ADaM and BIMO programming | G04 | source_data, specification, metadata | analysis_dataset, qc_evidence |
| tfl_results | Efficacy, safety, and TFL production | G05 | analysis_dataset, specification, metadata | output, reviewer_explanation |
| qc_validation | Risk-based QC and validation | G06 | analysis_dataset, output, metadata | qc_evidence, reviewer_explanation |
| reviewer_package | Reviewer explanation and regulatory package | G07, G08 | metadata, output, qc_evidence | reviewer_explanation, submission_package |
| platform_release | Platform engineering and release control | G09 | source_data, specification, metadata, analysis_dataset, output, qc_evidence, reviewer_explanation | qc_evidence, submission_package |

## Handoff Gates

| Gate | Name | Evidence layer | Description |
| --- | --- | --- | --- |
| G00 | governance_scope_lock | specification | Scope, authority, limitations, and readiness claims are aligned. |
| G01 | source_intake_lock | source_data | Source inventory, access limits, and source profiling are complete. |
| G02 | analysis_specification_lock | specification | Populations, endpoints, models, assumptions, and sensitivity rules are controlled. |
| G03 | metadata_lock | metadata | ADaM spec, Define-XML, CT, VLM, and traceability are internally consistent. |
| G04 | analysis_dataset_promotion | analysis_dataset | ADaM/BIMO datasets are built, logged, and reconciled or justified by risk. |
| G05 | output_promotion | output | TFLs and analysis results metadata are linked to datasets, programs, specs, and QC. |
| G06 | qc_signoff | qc_evidence | Risk-based validation, reconciliation, conformance, and known differences are complete. |
| G07 | reviewer_package_lock | reviewer_explanation | Reviewer guides explain data, methods, validation, conformance, and limitations. |
| G08 | submission_package_materialization | submission_package | eCTD-style package is generated from passed upstream gates. |
| G09 | release_candidate_lock | qc_evidence | Run record, hashes, environment, package manifest, and readiness statement are bound. |

## Workstream Required Artifacts

| Workstream | Artifact | Presence |
| --- | --- | --- |
| governance_scope | 02_specifications/sap/TROPIC_SAP_v4.0_industry_grade.docx | present |
| governance_scope | 06_qc_evidence/audit/SAP_LOCK_REVIEW_MEMO.md | present |
| governance_scope | docs/REGULATORY_WORKFLOW_RESEARCH.md | present |
| governance_scope | 06_qc_evidence/audit/findings_register.csv | present |
| governance_scope | 00_governance/REPRODUCIBILITY.md | present |
| governance_scope | README.md | present |
| governance_scope | config/validation_strategy.yaml | present |
| governance_scope | config/ctq_traceability.yaml | present |
| source_intake | 01_source_data | present |
| source_intake | 00_governance/REPRODUCIBILITY.md | present |
| source_intake | 04_analysis_datasets/programs/r/v_staging_ingest.R | present |
| source_intake | 04_analysis_datasets/programs/r/v_sdtm_validation.R | present |
| source_intake | platform/build_source_profile.py | present |
| statistical_specification | config/study_config.yaml | present |
| statistical_specification | 02_specifications/sap/TROPIC_SAP_v4.0_industry_grade.docx | present |
| statistical_specification | config/ctq_traceability.yaml | present |
| statistical_specification | 07_reviewer_explanation/analysis_report.md | present |
| statistical_specification | 07_reviewer_explanation/guides/TRACEABILITY_MATRIX.md | present |
| standards_metadata | 03_metadata/adam/ADaM_spec.xlsx | present |
| standards_metadata | 03_metadata/define/define.xml | present |
| standards_metadata | 03_metadata/define/define_sdtm.xml | present |
| standards_metadata | platform/gen_adam_labels.R | present |
| standards_metadata | 04_analysis_datasets/programs/sas/_adam_labels.sas | present |
| standards_metadata | 04_analysis_datasets/programs/r/adam_var_labels.csv | present |
| standards_metadata | 03_metadata/define/check_define_conformance.R | present |
| standards_metadata | 04_analysis_datasets/programs/r/spec_data_checks.R | present |
| standards_metadata | config/metadata_lineage.yaml | present |
| standards_metadata | platform/apply_metadata_lineage.py | present |
| standards_metadata | platform/build_metadata_control_report.py | present |
| adam_bimo_programming | 04_analysis_datasets/programs/sas | present |
| adam_bimo_programming | 04_analysis_datasets/programs/r | present |
| adam_bimo_programming | 04_analysis_datasets/adam | present |
| adam_bimo_programming | config/study_manifest.yaml | present |
| adam_bimo_programming | platform/cibuild.py | present |
| tfl_results | 05_outputs/tfl/tfl_generation.R | present |
| tfl_results | 05_outputs/tfl/tfl_stats.R | present |
| tfl_results | platform/build_tfl_output_index.py | present |
| tfl_results | 05_outputs/ars | present |
| qc_validation | 07_reviewer_explanation/guides/RISK_BASED_VALIDATION.md | present |
| qc_validation | config/validation_strategy.yaml | present |
| qc_validation | config/ctq_traceability.yaml | present |
| qc_validation | 06_qc_evidence/reconciliation | present |
| qc_validation | config/log_cleanliness.yaml | present |
| qc_validation | platform/check_log_cleanliness.py | present |
| qc_validation | platform/log_cleanliness/log_cleanliness_status.json | present |
| qc_validation | platform/verify_evidence.py | present |
| qc_validation | platform/conformance | present |
| reviewer_package | 07_reviewer_explanation/guides/ADRG.md | present |
| reviewer_package | 07_reviewer_explanation/guides/SDRG.md | present |
| reviewer_package | 07_reviewer_explanation/guides/BDRG.md | present |
| reviewer_package | 07_reviewer_explanation/analysis_report.md | present |
| reviewer_package | platform/package_ectd.py | present |
| reviewer_package | platform/build_ectd_backbone.py | present |
| reviewer_package | platform/materialize_ectd.py | present |
| platform_release | platform/cibuild.py | present |
| platform_release | platform/build_delivery_controls.py | present |
| platform_release | renv.lock | present |
| platform_release | config/evidence_layers.yaml | present |
| platform_release | platform/check_evidence_layers.py | present |
| platform_release | platform/check_delivery_model.py | present |
| platform_release | platform/build_delivery_dashboard.py | present |
| platform_release | platform/build_ctq_traceability_report.py | present |
| platform_release | platform/build_validation_strategy_report.py | present |
| platform_release | platform/build_release_candidate_checklist.py | present |
| platform_release | platform/build_orchestrator_gate_map.py | present |
| platform_release | platform/build_release_run_manifest.py | present |
| platform_release | config/log_cleanliness.yaml | present |
| platform_release | platform/check_log_cleanliness.py | present |
| platform_release | platform/log_cleanliness/log_cleanliness_status.json | present |
| platform_release | platform/release_run_manifest/release_run_manifest.json | present |
| platform_release | platform/release_run_manifest/release_run_files.csv | present |
| platform_release | 06_qc_evidence/audit/output_hash_binding.csv | present |

## Generated, External, Optional, and Planned Artifacts

| Layer | Status | Artifact | Presence | Matches | Role |
| --- | --- | --- | --- | --- | --- |
| source_data | external | 01_source_data/real_sdtm/*.sas7bdat | declared/excluded | n/a | Official de-identified SDTM source files; intentionally not redistributed. |
| source_data | external | 01_source_data/cbzp_reconstructed/*.rds | declared/excluded | n/a | Regenerable synthetic comparator artifacts; intentionally not committed. |
| source_data | optional | 01_source_data/reconstruct_cbzp_arm.R | present | 1 | Synthetic comparator reconstruction program, when present. |
| source_data | generated | docs/SOURCE_PROFILING_REPORT.md | present | 1 | Aggregate source profiling report. |
| source_data | generated | platform/source_profile_status.json | present | 1 | Machine-readable source profiling status. |
| source_data | generated | platform/source_profile/domain_inventory.csv | present | 1 | Aggregate source domain inventory. |
| source_data | generated | platform/source_profile/variable_profile.csv | present | 1 | Aggregate source variable profile. |
| metadata | generated | docs/METADATA_CONTROL_REPORT.md | present | 1 | Generated metadata governance report. |
| metadata | generated | platform/metadata_control/metadata_control_status.json | present | 1 | Machine-readable metadata governance status. |
| metadata | generated | platform/metadata_control/metadata_dataset_control.csv | present | 1 | Dataset-level metadata control extract. |
| metadata | generated | platform/metadata_control/metadata_findings.csv | present | 1 | Metadata governance findings extract. |
| metadata | generated | platform/metadata_lineage/metadata_lineage_status.json | present | 1 | Machine-readable lineage application/check status. |
| metadata | generated | platform/metadata_lineage/metadata_lineage_application.csv | present | 1 | Variable-level lineage check extract. |
| analysis_dataset | generated | 04_analysis_datasets/adam/*.xpt | present | 18 | Generated ADaM transport files. |
| analysis_dataset | generated | 04_analysis_datasets/datasetjson/**/*.json | present | 43 | Generated Dataset-JSON metadata and data files. |
| analysis_dataset | generated | 04_analysis_datasets/datasetjson/**/*.ndjson | present | 43 | Generated Dataset-JSON NDJSON payload files. |
| output | generated | 05_outputs/tfl/TFL_Gallery.html | present | 1 | Rendered TFL gallery. |
| output | generated | 05_outputs/tfl/output | present | 1 | Rendered table/figure/listing output directory. |
| output | generated | 05_outputs/ars/tropic_ard.csv | present | 1 | Analysis Results Standard ARD. |
| output | generated | 05_outputs/ars/tropic_reporting_event.json | present | 1 | Analysis Results Standard reporting event. |
| output | generated | 03_metadata/usdm/tropic_usdm.json | present | 1 | USDM study definition export. |
| output | generated | docs/TFL_OUTPUT_INDEX.md | present | 1 | Structured TFL output traceability index. |
| output | generated | platform/tfl_output_index_status.json | present | 1 | Machine-readable TFL output index status. |
| output | generated | platform/tfl_output_index/tfl_output_index.csv | present | 1 | CSV TFL output traceability index. |
| output | generated | platform/tfl_output_index/tfl_output_index.json | present | 1 | JSON TFL output traceability index. |
| qc_evidence | generated | platform/pipeline_health.json | present | 1 | Latest run health record. |
| qc_evidence | generated | platform/reconciliation_status.json | present | 1 | Dataset-level reconciliation status. |
| qc_evidence | generated | platform/results_reconciliation_status.json | present | 1 | Results-level reconciliation status. |
| qc_evidence | generated | platform/conformance/spec_define_conformance.json | present | 1 | Spec-to-define conformance result. |
| qc_evidence | generated | platform/conformance/spec_data_conformance.json | present | 1 | Spec-to-data conformance result. |
| qc_evidence | generated | platform/release_run_manifest/release_run_manifest.json | present | 1 | Machine-readable current release-run manifest and hash seal. |
| qc_evidence | generated | platform/release_run_manifest/release_run_files.csv | present | 1 | Per-file hash ledger bound into the release-run manifest. |
| qc_evidence | generated | docs/RELEASE_RUN_MANIFEST.md | present | 1 | Reviewer-readable release-run manifest summary. |
| qc_evidence | generated | docs/RELEASE_CANDIDATE_CHECKLIST.md | present | 1 | Generated release-candidate go/no-go checklist. |
| qc_evidence | generated | docs/VALIDATION_STRATEGY_CONTROL_REPORT.md | present | 1 | Generated risk-based validation strategy control report. |
| qc_evidence | generated | docs/CTQ_TRACEABILITY_REPORT.md | present | 1 | Generated CTQ and estimand traceability report. |
| qc_evidence | generated | platform/ctq_traceability/ctq_traceability_status.json | present | 1 | Machine-readable CTQ traceability status. |
| qc_evidence | generated | platform/ctq_traceability/ctq_traceability_checks.csv | present | 1 | CSV CTQ traceability check results. |
| qc_evidence | generated | platform/validation_strategy/validation_strategy_status.json | present | 1 | Machine-readable risk-based validation strategy status. |
| qc_evidence | generated | platform/validation_strategy/validation_strategy_checks.csv | present | 1 | CSV evidence check results for the validation strategy. |
| qc_evidence | generated | docs/LOG_CLEANLINESS_REPORT.md | present | 1 | Generated SAS/R execution-log cleanliness report. |
| qc_evidence | generated | platform/log_cleanliness/log_cleanliness_status.json | present | 1 | Machine-readable log-cleanliness gate status. |
| qc_evidence | generated | platform/log_cleanliness/log_findings.csv | present | 1 | CSV log-cleanliness findings and reviewed exceptions. |
| qc_evidence | generated | platform/release_candidate/release_candidate_status.json | present | 1 | Machine-readable release-candidate status. |
| qc_evidence | generated | platform/release_candidate/release_candidate_checklist.csv | present | 1 | CSV release-candidate checklist. |
| qc_evidence | generated | docs/ORCHESTRATOR_GATE_MAP.md | present | 1 | Generated map from runtime DAG stages to delivery gates. |
| qc_evidence | generated | platform/orchestrator_gate_map/orchestrator_gate_map_status.json | present | 1 | Machine-readable orchestrator gate-map status. |
| qc_evidence | generated | platform/orchestrator_gate_map/orchestrator_gate_map.csv | present | 1 | CSV orchestrator stage-to-gate map. |
| reviewer_explanation | generated | docs/DELIVERY_EVIDENCE_DASHBOARD.md | present | 1 | Generated delivery/evidence architecture dashboard. |
| submission_package | generated | 08_submission_package/m5 | present | 1 | Current eCTD Module 5 style payload tree. |
| submission_package | generated | 08_submission_package/ectd/0000 | present | 1 | Materialized sequence 0000. |
| submission_package | generated | 08_submission_package/ectd/RUN_RECORD.md | present | 1 | eCTD materialization run record. |

## Missing Required Artifacts

No required workstream artifacts are missing.

## Missing Required Evidence-Layer Artifacts

No required evidence-layer artifacts are missing.

## Interpretation Rules

- `required` artifacts must exist for the architecture check to pass.
- `generated` artifacts may be absent in a clean clone and should be produced by the pipeline.
- `external` artifacts are intentionally excluded from git, usually because they are patient data, governed inputs, or credentials.
- `optional` artifacts are useful but not required for the architecture check.
- `planned` artifacts document target-state work that is not yet implemented.
