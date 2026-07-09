# TROPIC Metadata Control Report

Generated: 2026-07-09 16:40:36 UTC

> Metadata governance view across ADaM spec, Define-XML, ARM/ARS, conformance outputs, and traceability evidence. This report exposes both passing controls and unresolved metadata gaps.

## Summary

| Item | Value |
| --- | --- |
| Report status | pass |
| Spec datasets | 7 |
| Spec variables | 159 |
| Spec value-level rows | 7 |
| Spec codelist terms | 60 |
| Spec methods | 46 |
| ADaM Define ItemGroupDefs | 7 |
| ADaM Define ItemDefs | 166 |
| ADaM ARM ResultDisplays | 8 |
| ADaM ARM AnalysisResults | 10 |
| SDTM Define ItemGroupDefs | 18 |
| ARS ARD rows | 16 |

## Conformance Status

| Control | Status | Findings/violations |
| --- | --- | --- |
| Spec -> Define | PASS | 0 |
| Spec -> Data | PASS |  |
| CT cross-validation | WARNING | 0 |
| CT disposition register | PASS | 2 sponsor-defined dispositions |
| ADaM conformance status | PASS (0 errors at this check level) | 0 |

## Controlled Terminology Dispositions

| Codelist | Status | Applies to | Rationale |
| --- | --- | --- | --- |
| CL.CNSR | sponsor_defined | ADTTE.CNSR | Time-to-event censoring indicator where 0 denotes event and 1 denotes censored. The values support ADTTE derivations and SAS/R reconciliation.  |
| CL.TRT01PN | sponsor_defined | ADSL.TRT01PN, ADEX.TRT01PN, ADTTE.TRT01PN | Numeric treatment ordering used for analysis, sorting, and reconciliation. Treatment text values remain reviewer-facing in TRT01P/TRT01A/TRTA.  |

## Dataset Metadata Control

| Dataset | Class | Spec vars | Data vars | Spec-data status | CT violations | Type mismatches | Length mismatches |
| --- | --- | --- | --- | --- | --- | --- | --- |
| ADSL | SUBJECT LEVEL ANALYSIS DATASET | 42 | 42 | PASS | 0 | 0 | 0 |
| ADEX | BASIC DATA STRUCTURE | 14 | 14 | PASS | 0 | 0 | 0 |
| ADCM | OCCURRENCE DATA STRUCTURE | 15 | 15 | PASS | 0 | 0 | 0 |
| ADAE | OCCURRENCE DATA STRUCTURE | 29 | 29 | PASS | 0 | 0 | 0 |
| ADLB | BASIC DATA STRUCTURE | 27 | 27 | PASS | 0 | 0 | 0 |
| ADRS | BASIC DATA STRUCTURE | 13 | 13 | PASS | 0 | 0 | 0 |
| ADTTE | BASIC DATA STRUCTURE | 19 | 19 | PASS | 0 | 0 | 0 |

## Spec Variable Origin Profile

| Origin | Variables |
| --- | --- |
| Assigned | 16 |
| Collected | 94 |
| Derived | 42 |
| Protocol | 7 |

## Traceability Extract Status

| Traceability status | Variables |
| --- | --- |
| DOCUMENTED | 159 |

## Metadata Findings

No metadata governance findings were detected.

## Machine-Readable Outputs

- `platform/metadata_control/metadata_control_status.json`
- `platform/metadata_control/metadata_dataset_control.csv`
- `platform/metadata_control/metadata_findings.csv`
