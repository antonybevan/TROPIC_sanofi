# Pinnacle 21 Community ADaM Validation Run Record

**Record ID:** TROPIC-P21-ADAM-2026-08-12-01

**Execution date:** 2026-08-12

**Status:** `EXECUTED_WITH_COMPATIBILITY_CAVEAT`

**Use:** `INFORMATIVE_ONLY`

**Licensed Enterprise execution:** `NOT_EXECUTED`

## Controlled execution

| Item | Recorded value |
|---|---|
| Application | Pinnacle 21 Community 4.1.0, build 4.1.0.4652 |
| Distribution verification | Apple notarized Developer ID, Pinnacle 21 LLC, Team ID `56C9Z22DN3` |
| Client component | `p21-client-1.0.8.jar`; SHA-256 `1d6cb1c03c16bb7dec2c2e04933fc1dcd01bcad8781c456000434cee0173e8b7` |
| Validation engine | FDA 2508.1 |
| Standard | ADaMIG 1.3 (FDA) |
| Controlled terminology | ADaM and SDTM CT 2024-03-29 |
| Define-XML | `03_metadata/define/define.xml`; SHA-256 `e95ec20c86556c442f6e0381dc5bbc0a5f74eff66688629f454d6224b270783a` |
| Inputs | Seven real MP-arm production XPTs: ADAE, ADCM, ADEX, ADLB, ADRS, ADSL, ADTTE |
| Scope | 121,320 records; 7 of 7 datasets processed |
| Checks | 5,546 checks executed |
| Result | 37 issue-summary messages |
| Raw report | `pinnacle21-report-2026-08-12T12-24-20-781.xlsx`; SHA-256 `0beb2835708061db3f58bb5ddeda45ce46f5008f25fea58e2c1601225ed8c823` |

The raw workbook is retained outside Git because its issue tabs include record-level subject identifiers. The repository records the run identity, hashes, aggregate result, and disposition without redistributing patient-level rows.

## Compatibility caveat

The official Community GUI completed the validation using the current downloaded 2508.1 engine. The generated Validation Summary nevertheless reports **`Incompatible CLI used`**. Accordingly:

- this run is real execution evidence, not a placeholder;
- it is not represented as licensed Pinnacle 21 Enterprise validation;
- it is not submission-clearance evidence;
- numeric severity rendering and issue classification must not be treated as authoritative until reproduced in a compatible, qualified environment.

## Aggregate disposition

| Group | Observation | Disposition |
|---|---|---|
| Traceability | GLOBAL messages note that DM/AE/EX source domains were not supplied with this ADaM-only run. | Expected for this scoped run; a licensed final run must include the complete locked source/metadata context. |
| Yes-only flags | `TRTEMFL='N'` in ADAE/ADCM and `ANL01FL='N'` in ADLB generated the dominant record counts. | Corrected in paired SAS/R source to use `Y`/null; rerun required after the controlled rebuild. |
| Date chronology | Six ADAE rows have start dates after end dates; additional day-zero observations were reported in ADCM/ADLB/ADRS. | Source/derivation review required. No silent clinical-data correction is permitted without an approved rule. |
| Metadata and labels | Dataset/variable labels, predecessor variables, and Define datatype differences were reported across the seven datasets. | Open for standards triage against ADaMIG, source traceability, and the authoritative specification. |
| Value representation | ADEX/ADLB/ADRS inconsistencies between numeric and character analysis values were reported. | Open modeling issue; correct only through an approved specification change and paired implementation. |
| Controlled terminology | ADAE action-taken terminology and related metadata messages were reported. | Open for source-to-CT review and ADRG disposition. |

## Qualification decision

- `PINNACLE21_COMMUNITY=INFORMATIVE_ONLY`
- `LICENSED_PINNACLE21_ENTERPRISE=NOT_EXECUTED`
- `SUBMISSION_CLEARANCE=NOT_CLAIMED`

The final regulated-use closure path is defined in `docs/QUALITY_SYSTEM_BOUNDARY.md`.
