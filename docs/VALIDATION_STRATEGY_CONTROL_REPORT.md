# TROPIC Validation Strategy Control Report

Generated: 2026-07-09 15:02:26 UTC

> This report evaluates `validation_strategy.yaml`: the machine-readable risk-based, traceability-driven, specification-controlled validation strategy. A BLOCKED status means the current evidence set cannot support a release-ready claim.

## Verdict

| Item | Value |
| --- | --- |
| Overall status | PASS |
| Artifacts assessed | 11 |
| Pass | 11 |
| Blocked | 0 |

## Artifact Strategy Status

| Artifact | Risk | Gate | Owner | Status | Checks pass | Checks fail | Decision impact |
| --- | --- | --- | --- | --- | --- | --- | --- |
| source_profile | high | G01 | clinical_data_management | PASS | 1 | 0 | Controls source inventory, subject count, critical variable presence, and intake readiness. |
| adsl | critical | G04 | statistical_programming | PASS | 5 | 0 | Defines populations, treatment anchors, demographics, and subject-level covariates used across all analyses. |
| adtte_primary | critical | G04 | statistical_programming | PASS | 7 | 0 | Primary efficacy interpretation and headline time-to-event evidence. |
| adtte_secondary | high | G04 | statistical_programming | PASS | 5 | 0 | Important supportive efficacy interpretation. |
| safety_adam | high | G04 | statistical_programming | PASS | 4 | 0 | Safety summaries, exposure context, adverse-event interpretation, and labeling-relevant review. |
| response_adam | high | G04 | statistical_programming | PASS | 4 | 0 | Response endpoint interpretation and responder evidence. |
| tfl_primary_secondary | critical | G05 | statistical_programming | PASS | 5 | 0 | Reviewer-facing efficacy/safety results. |
| metadata_package | critical | G03 | standards_metadata | PASS | 4 | 0 | Controls reviewer ability to understand, navigate, and reproduce submitted datasets. |
| reviewer_explanation | high | G07 | medical_writing_regulatory | PASS | 6 | 0 | Explains methods, limitations, conformance findings, and review path. |
| log_cleanliness | high | G06 | qc_validation | PASS | 1 | 0 | Prevents unapproved execution-log warnings or data-conversion notes from being hidden beneath passing reconciliation telemetry. |
| platform_release_controls | critical | G09 | platform_release | PASS | 4 | 0 | Determines whether the current run can be treated as a release candidate. |

## Evidence Checks

| Artifact | Check | Status | File | Field | Actual | Expected | Evidence |
| --- | --- | --- | --- | --- | --- | --- | --- |
| source_profile | source_profile_pass | PASS | 06_telemetry/source_profile_status.json | status | pass | pass | Source profile completed without findings. |
| adsl | current_real_sas | PASS | 06_telemetry/pipeline_health.json | sas_execution_mode | oda | ['oda', 'local'] | Current live run used an independent SAS engine. |
| adsl | dataset_reconciliation_pass | PASS | 06_telemetry/reconciliation_status.json | overall | PASS | PASS | Dataset-level reconciliation passed. |
| adsl | dataset_reconciliation_not_simulated | PASS | 06_telemetry/reconciliation_status.json | simulated | False | False | Dataset-level reconciliation is not a byte-copy simulation. |
| adsl | admiral_adsl_pass | PASS | 06_telemetry/admiral_reconciliation_status.json | domains.ADSL.status | PASS | PASS | Third-engine ADSL reconciliation passed. |
| adsl | spec_data_pass | PASS | 06_telemetry/conformance/spec_data_conformance.json | status | PASS | PASS | ADaM specification matches produced data. |
| adtte_primary | current_real_sas | PASS | 06_telemetry/pipeline_health.json | sas_execution_mode | oda | ['oda', 'local'] | Current live run used an independent SAS engine. |
| adtte_primary | dataset_reconciliation_pass | PASS | 06_telemetry/reconciliation_status.json | overall | PASS | PASS | Dataset-level reconciliation passed. |
| adtte_primary | dataset_reconciliation_not_simulated | PASS | 06_telemetry/reconciliation_status.json | simulated | False | False | Dataset-level reconciliation is not a byte-copy simulation. |
| adtte_primary | results_reconciliation_pass | PASS | 06_telemetry/results_reconciliation_status.json | overall | PASS | PASS | Numerical results reconciliation passed. |
| adtte_primary | admiral_os_pass | PASS | 06_telemetry/admiral_reconciliation_status.json | domains.ADTTE.OS.status | PASS | PASS | Third-engine OS reconciliation passed. |
| adtte_primary | admiral_pfs_pass | PASS | 06_telemetry/admiral_reconciliation_status.json | domains.ADTTE.PFS.status | PASS | PASS | Third-engine PFS reconciliation passed. |
| adtte_primary | spec_data_pass | PASS | 06_telemetry/conformance/spec_data_conformance.json | status | PASS | PASS | ADaM specification matches produced data. |
| adtte_secondary | current_real_sas | PASS | 06_telemetry/pipeline_health.json | sas_execution_mode | oda | ['oda', 'local'] | Current live run used an independent SAS engine. |
| adtte_secondary | dataset_reconciliation_pass | PASS | 06_telemetry/reconciliation_status.json | overall | PASS | PASS | Dataset-level reconciliation passed. |
| adtte_secondary | dataset_reconciliation_not_simulated | PASS | 06_telemetry/reconciliation_status.json | simulated | False | False | Dataset-level reconciliation is not a byte-copy simulation. |
| adtte_secondary | results_reconciliation_pass | PASS | 06_telemetry/results_reconciliation_status.json | overall | PASS | PASS | Numerical results reconciliation passed. |
| adtte_secondary | spec_data_pass | PASS | 06_telemetry/conformance/spec_data_conformance.json | status | PASS | PASS | ADaM specification matches produced data. |
| safety_adam | current_real_sas | PASS | 06_telemetry/pipeline_health.json | sas_execution_mode | oda | ['oda', 'local'] | Current live run used an independent SAS engine. |
| safety_adam | dataset_reconciliation_pass | PASS | 06_telemetry/reconciliation_status.json | overall | PASS | PASS | Dataset-level reconciliation passed. |
| safety_adam | dataset_reconciliation_not_simulated | PASS | 06_telemetry/reconciliation_status.json | simulated | False | False | Dataset-level reconciliation is not a byte-copy simulation. |
| safety_adam | spec_data_pass | PASS | 06_telemetry/conformance/spec_data_conformance.json | status | PASS | PASS | ADaM specification matches produced data. |
| response_adam | current_real_sas | PASS | 06_telemetry/pipeline_health.json | sas_execution_mode | oda | ['oda', 'local'] | Current live run used an independent SAS engine. |
| response_adam | dataset_reconciliation_pass | PASS | 06_telemetry/reconciliation_status.json | overall | PASS | PASS | Dataset-level reconciliation passed. |
| response_adam | dataset_reconciliation_not_simulated | PASS | 06_telemetry/reconciliation_status.json | simulated | False | False | Dataset-level reconciliation is not a byte-copy simulation. |
| response_adam | spec_data_pass | PASS | 06_telemetry/conformance/spec_data_conformance.json | status | PASS | PASS | ADaM specification matches produced data. |
| tfl_primary_secondary | tfl_index_pass | PASS | 06_telemetry/tfl_output_index_status.json | status | pass | pass | TFL output index is complete for controlled catalog scope (tfl_output_catalog.yaml). |
| tfl_primary_secondary | ctq_traceability_pass | PASS | 06_telemetry/ctq_traceability/ctq_traceability_status.json | status | PASS | PASS | CTQ/estimand traceability links clinical questions to ADaM, outputs, reviewer guides, and validation evidence. |
| tfl_primary_secondary | results_reconciliation_pass | PASS | 06_telemetry/results_reconciliation_status.json | overall | PASS | PASS | Numerical results reconciliation passed. |
| tfl_primary_secondary | forest_reconciliation_pass | PASS | 06_telemetry/forest_reconciliation_status.json | overall | PASS | PASS | Forest HR result reconciliation passed. |
| tfl_primary_secondary | cbzp_bridge_pass | PASS | 06_telemetry/cbzp_bridge_status.json | overall | PASS | PASS | Synthetic comparator bridge parity passed. |
| metadata_package | spec_define_pass | PASS | 06_telemetry/conformance/spec_define_conformance.json | status | PASS | PASS | ADaM specification matches Define-XML. |
| metadata_package | spec_data_pass | PASS | 06_telemetry/conformance/spec_data_conformance.json | status | PASS | PASS | ADaM specification matches produced data. |
| metadata_package | ctq_traceability_pass | PASS | 06_telemetry/ctq_traceability/ctq_traceability_status.json | status | PASS | PASS | CTQ/estimand traceability links clinical questions to ADaM, outputs, reviewer guides, and validation evidence. |
| metadata_package | metadata_control_pass | PASS | 06_telemetry/metadata_control/metadata_control_status.json | status | pass | pass | Metadata control has no unresolved warning/blocking findings. |
| reviewer_explanation | ctq_traceability_pass | PASS | 06_telemetry/ctq_traceability/ctq_traceability_status.json | status | PASS | PASS | CTQ/estimand traceability links clinical questions to ADaM, outputs, reviewer guides, and validation evidence. |
| reviewer_explanation | file:08_reviewers_guides/ADRG.md | PASS | 08_reviewers_guides/ADRG.md |  | present | present | Required reviewer/documentation artifact is present. |
| reviewer_explanation | file:08_reviewers_guides/SDRG.md | PASS | 08_reviewers_guides/SDRG.md |  | present | present | Required reviewer/documentation artifact is present. |
| reviewer_explanation | file:08_reviewers_guides/BDRG.md | PASS | 08_reviewers_guides/BDRG.md |  | present | present | Required reviewer/documentation artifact is present. |
| reviewer_explanation | file:08_reviewers_guides/SDSP.md | PASS | 08_reviewers_guides/SDSP.md |  | present | present | Required reviewer/documentation artifact is present. |
| reviewer_explanation | file:08_reviewers_guides/TRACEABILITY_MATRIX.md | PASS | 08_reviewers_guides/TRACEABILITY_MATRIX.md |  | present | present | Required reviewer/documentation artifact is present. |
| log_cleanliness | log_cleanliness_pass | PASS | 06_telemetry/log_cleanliness/log_cleanliness_status.json | status | PASS | PASS | SAS/R execution logs contain no unapproved errors, warnings, invalid-input notes, uninitialized variables, or risky conversion/merge notes. |
| platform_release_controls | pipeline_green | PASS | 06_telemetry/pipeline_health.json | pipeline_health_status | GREEN | GREEN | Current pipeline health is green. |
| platform_release_controls | current_real_sas | PASS | 06_telemetry/pipeline_health.json | sas_execution_mode | oda | ['oda', 'local'] | Current live run used an independent SAS engine. |
| platform_release_controls | dataset_reconciliation_not_simulated | PASS | 06_telemetry/reconciliation_status.json | simulated | False | False | Dataset-level reconciliation is not a byte-copy simulation. |
| platform_release_controls | log_cleanliness_pass | PASS | 06_telemetry/log_cleanliness/log_cleanliness_status.json | status | PASS | PASS | SAS/R execution logs contain no unapproved errors, warnings, invalid-input notes, uninitialized variables, or risky conversion/merge notes. |

## Machine-Readable Outputs

- `06_telemetry/validation_strategy/validation_strategy_status.json`
- `06_telemetry/validation_strategy/validation_strategy_checks.csv`
