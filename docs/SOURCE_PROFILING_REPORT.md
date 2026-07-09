# TROPIC Source Profiling Report

Generated: 2026-07-09 16:40:31 UTC

> Aggregate-only source profiling evidence. This report does not print patient-level records or subject identifiers.

## Scope

| Item | Value |
| --- | --- |
| Source directory | 01_source_data/real_sdtm |
| Status | pass |
| SAS7BDAT domains | 34 |
| Total records across domains | 458333 |
| Total source bytes | 209854464 |
| DM unique subjects | 371 |

## Domain Inventory

| Domain | Records | Variables | USUBJID n | Profile key | Duplicate key records | Date vars | Week precision vars | Expected missing |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| AE | 5428 | 29 | 357 | USUBJID+AESEQ | 0 | 0 | 4 |  |
| CD | 3339 | 14 | 371 | USUBJID+CDSEQ | 0 | 1 | 0 |  |
| CM | 24534 | 18 | 371 | USUBJID+CMSEQ | 0 | 2 | 0 |  |
| CX | 2516 | 21 | 371 | USUBJID+CXSEQ | 0 | 1 | 0 |  |
| DM | 371 | 12 | 371 | USUBJID | 0 | 2 | 0 |  |
| DS | 2842 | 14 | 371 | USUBJID+DSSEQ | 0 | 0 | 2 |  |
| EG | 558 | 15 | 352 | USUBJID+EGSEQ | 0 | 1 | 0 |  |
| EX | 3485 | 16 | 371 | USUBJID+EXSEQ | 0 | 2 | 0 |  |
| IE | 42 | 13 | 38 | USUBJID+IESEQ | 0 | 0 | 0 |  |
| LB | 80788 | 27 | 371 | USUBJID+LBSEQ | 0 | 1 | 0 |  |
| LS | 5774 | 21 | 371 | USUBJID+LSSEQ | 0 | 1 | 0 |  |
| MH | 2292 | 13 | 346 | USUBJID+MHSEQ | 0 | 1 | 0 |  |
| PE | 3614 | 17 | 371 | USUBJID+PESEQ | 0 | 1 | 0 |  |
| PN | 26982 | 18 | 358 | USUBJID+PNSEQ | 0 | 1 | 0 |  |
| PR | 151 | 10 | 65 | USUBJID+PRSEQ | 0 | 1 | 0 |  |
| SC | 11 | 11 | 11 | USUBJID+SCSEQ | 0 | 1 | 0 |  |
| SUPPAE | 53153 | 11 | 357 | USUBJID+RDOMAIN+QNAM+IDVARVAL | 0 | 0 | 0 |  |
| SUPPCM | 108333 | 11 | 371 | USUBJID+RDOMAIN+QNAM+IDVARVAL | 0 | 0 | 0 |  |
| SUPPDM | 2597 | 11 | 371 | USUBJID+RDOMAIN+QNAM+IDVARVAL | 0 | 0 | 0 |  |
| SUPPDS | 1083 | 11 | 338 | USUBJID+RDOMAIN+QNAM+IDVARVAL | 0 | 0 | 0 |  |
| SUPPEG | 164 | 11 | 118 | USUBJID+RDOMAIN+QNAM+IDVARVAL | 0 | 0 | 0 |  |
| SUPPEX | 18137 | 11 | 371 | USUBJID+RDOMAIN+QNAM+IDVARVAL | 0 | 0 | 0 |  |
| SUPPIE | 21 | 11 | 21 | USUBJID+RDOMAIN+QNAM+IDVARVAL | 0 | 0 | 0 |  |
| SUPPLB | 80788 | 11 | 371 | USUBJID+RDOMAIN+QNAM+IDVARVAL | 0 | 0 | 0 |  |
| SUPPLS | 5610 | 11 | 367 | USUBJID+RDOMAIN+QNAM+IDVARVAL | 0 | 0 | 0 |  |
| SUPPMH | 2025 | 11 | 326 | USUBJID+RDOMAIN+QNAM+IDVARVAL | 0 | 0 | 0 |  |
| SUPPPE | 1134 | 11 | 368 | USUBJID+RDOMAIN+QNAM+IDVARVAL | 0 | 0 | 0 |  |
| SUPPPR | 151 | 11 | 65 | USUBJID+RDOMAIN+QNAM+IDVARVAL | 0 | 0 | 0 |  |
| SV | 3930 | 9 | 371 | USUBJID+VISITNUM | 0 | 2 | 0 |  |
| TE | 4 | 6 |  | STUDYID+ETCD | 0 | 0 | 0 |  |
| TI | 48 | 5 |  | STUDYID+IETESTCD | 0 | 0 | 0 |  |
| TS | 16 | 6 |  | STUDYID+TSPARMCD | 0 | 0 | 0 |  |
| TV | 24 | 7 |  | STUDYID+ARMCD+VISITNUM | 0 | 0 | 0 |  |
| VS | 18388 | 19 | 371 | USUBJID+VSSEQ | 0 | 1 | 0 |  |

## Source Control Findings

No duplicate records were detected under the selected profiling keys.

## Expected Variable Availability

All configured critical expected variables are present in the profiled domains.

## High Missingness Among Critical Expected Variables

| Domain | Variable | Missing n | Missing % |
| --- | --- | --- | --- |
| CM | CMENDTC | 16344 | 66.62 |
| CM | CMSTDTC | 12944 | 52.76 |
| AE | AESER | 1137 | 20.95 |
| AE | AEREL | 1136 | 20.93 |

## Timing-Variable Notes

Date-like variables were detected by `*DTC`/`*DT` suffixes; study-day variables by `*DY`; week-precision variables by `*WK`/`*WKF`.
Week-precision variables should continue to be disclosed in reviewer documentation because they can affect event-time derivations.

## Machine-Readable Outputs

- `platform/source_profile_status.json`
- `platform/source_profile/domain_inventory.csv`
- `platform/source_profile/variable_profile.csv`
