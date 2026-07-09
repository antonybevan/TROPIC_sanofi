# TROPIC CTQ and Estimand Traceability Report

Generated: 2026-07-09 14:50:44 UTC

> This report evaluates `ctq_traceability.yaml`, linking clinical questions to estimand-style attributes, ADaM inputs, TFL/ARS outputs, reviewer guides, and validation-strategy artifacts.

## Verdict

| Item | Value |
| --- | --- |
| Overall status | PASS |
| CTQ factors | 8 |
| Pass | 8 |
| Warning | 0 |
| Fail | 0 |

## CTQ Traceability Matrix

| CTQ | Domain | Risk | Status | ADaM datasets | Outputs | Validation artifacts |
| --- | --- | --- | --- | --- | --- | --- |
| CTQ-EFF-OS | efficacy | critical | PASS | ADSL, ADTTE | F-11-1, F-12-1 | adtte_primary, adsl, tfl_primary_secondary |
| CTQ-EFF-PFS | efficacy | critical | PASS | ADSL, ADTTE | F-11-2 | adtte_primary, adsl, tfl_primary_secondary |
| CTQ-EFF-SECONDARY-TTE | efficacy | high | PASS | ADSL, ADTTE | T-11-6, T-11-7 | adtte_secondary, adsl, tfl_primary_secondary |
| CTQ-EFF-RESPONSE | efficacy | high | PASS | ADSL, ADRS, ADLB | T-11-8, T-11-8b, F-13-1 | response_adam, safety_adam, tfl_primary_secondary |
| CTQ-SAFE-TEAE | safety | high | PASS | ADSL, ADAE | T-20-1, T-20-2 | safety_adam, adsl |
| CTQ-SAFE-LAB | safety | high | PASS | ADSL, ADLB | T-21-1, T-21-2 | safety_adam |
| CTQ-SAFE-EXPOSURE | safety | high | PASS | ADSL, ADEX, ADLB, ADTTE | F-14-1, F-17-1, T-17-1, T-17-2, T-17-4 | safety_adam, adtte_secondary |
| CTQ-META-REVIEWABILITY | metadata | critical | PASS | ADSL, ADEX, ADCM, ADAE, ADLB, ADRS, ADTTE | n/a | metadata_package, reviewer_explanation, platform_release_controls |

## Findings

| CTQ | Status | Message |
| --- | --- | --- |
| CTQ-EFF-OS | PASS | CTQ traceability complete |
| CTQ-EFF-PFS | PASS | CTQ traceability complete |
| CTQ-EFF-SECONDARY-TTE | PASS | CTQ traceability complete |
| CTQ-EFF-RESPONSE | PASS | CTQ traceability complete |
| CTQ-SAFE-TEAE | PASS | CTQ traceability complete |
| CTQ-SAFE-LAB | PASS | CTQ traceability complete |
| CTQ-SAFE-EXPOSURE | PASS | CTQ traceability complete |
| CTQ-META-REVIEWABILITY | PASS | CTQ traceability complete |

## Machine-Readable Outputs

- `06_telemetry/ctq_traceability/ctq_traceability_status.json`
- `06_telemetry/ctq_traceability/ctq_traceability_checks.csv`
