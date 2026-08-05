# F-042 CM/PR Radiotherapy Source Qualification Audit

**Audit ID:** `F042-PR-SOURCE-QUAL-2026-08-03`<br>
**Version:** `0.2.0`<br>
**Status:** **ED-02 ADOPTED — PATH A IMPLEMENTATION SEALED; EXTERNAL QUALIFIED REVIEW REQUIRED**<br>
**Parent decision:** [`ENDPOINT_DECISION_RECORD_F042_T11_8_2026-08-03.md`](ENDPOINT_DECISION_RECORD_F042_T11_8_2026-08-03.md)<br>
**Approval dependency:** `ED-02` — PR source, precedence, intent, and date handling<br>
**Product path:** Path A controlled non-submission demonstration

> **Historical baseline notice (2026-08-05):** Sections 1–5 retain the pre-implementation staging-readiness assessment. The closure addendum below controls the current status: the adopted CM+PR implementation, full real-SAS rerun, release reseal, and CI verification are complete. This remains a single-author Path A demonstration; external qualified statistical/medical review is outstanding.

## 1. Audit purpose

This audit establishes whether the raw SDTM PR domain and the staged CM domain are technically available and linkable for a future author-adopted Path A palliative-radiotherapy rule. It is a source-quality and staging-readiness assessment only.

It does not classify treatment intent, decide whether a procedure is palliative for pain, define a PFS event window, or change the current ADTTE/TFL outputs.

## 2. Source and baseline

| Item | Observed value |
|---|---|
| Raw source | `01_source_data/real_sdtm/pr.sas7bdat` |
| Domain | `PR` |
| Study | `EFC6193` |
| Rows | 151 |
| Distinct subjects | 65 |
| Distinct `PRTRT` terms | 106 |
| `PRCAT` | `OTHER PROCEDURES` for all 151 rows |
| Visit representation | `VISITNUM=99`, `VISIT=UNSCHEDULED` for all 151 rows |
| `PRDTC` non-missing | 151/151 |
| Complete ISO `PRDTC` | 148/151 |
| Year-month `PRDTC` | 3/151; no day imputation performed |
| Duplicate `USUBJID/PRSEQ` keys | 0 |
| `USUBJID` to `SUBJID` mapping | 151/151 consistent |
| PR subjects mapped to ADSL | 65/65 |
| PR subjects in real MP ITT | 65/65 |

The three partial dates are year-month values on non-radiation procedures. All 11 radiation-screened rows have complete ISO dates.

## 3. Radiation screening and linkage

The descriptive radiation screen uses `PRTRT` terms containing `radi` (case-insensitive). This is a source inventory screen, not a palliative-RT qualification rule.

| Screen | Result |
|---|---:|
| Radiation-screened PR rows | 11 |
| Subjects with radiation-screened PR rows | 9 |
| `PALLIATIVE RADIATION TO SPINE` rows | 3 |
| Radiation-screened rows complete ISO dated | 11/11 |
| Radiation-screened rows after `RANDDT` | 11/11 |
| Radiation-screened rows after `TRTSDT` | 11/11 |
| Current real-MP PFS pain candidates | 37 |
| Pain-candidate subjects with any radiation PR row | 1 |
| Radiation PR rows on or before that subject’s pain event | 0 |
| Radiation PR rows after that pain event | 3; 23–25 days later |

The date-only linkage does not answer whether a later procedure should alter an earlier pain event.

### 3.1 Direct-intent CM/PR review

The decision review identified source text containing both a radiation concept and an explicit `PALLIATIVE` or `ANTALGIC` intent term. This narrow screen avoids false-positive matches such as estradiol, generic historical radiotherapy and radiopharmaceutical terms.

| Direct-intent screen | CM | PR |
|---|---:|---:|
| Rows | 13 | 3 |
| Distinct subjects | 10 | 1 |
| Complete start dates | 12 | 3 |
| Complete dates after `RANDDT` | 12 | 3 |
| Complete dates on/before `RANDDT` | 0 | 0 |
| Subjects overlapping across CM and PR | 0 | 0 |

All 13 direct-intent CM rows are categorized as post-treatment anti-cancer therapy. Twelve have complete start dates; one has a recorded end date but no start date. The latter cannot enter the primary exact-date event derivation.

The direct-intent CM and PR subject sets do not overlap. Therefore, the prior proposal to make PR the sole or presumptive primary endpoint source would omit distinct CM evidence and is rejected. The author-decision-ready proposal uses a CM+PR union with source-level provenance.

## 4. Staging-readiness assessment

| Control | Result | Disposition |
|---|---|---|
| Preserve complete PR domain | 151/151 rows available | **Required** — do not ingest only radiation terms. |
| Preserve complete CM domain | Existing staged CM contains source and supplemental variables | **Required** — do not reduce CM to broad text matches. |
| Preserve source text | PR and CM treatment/category/intent/date fields are present | **Required** — no recoding of treatment intent at ingest. |
| Date derivation | 148 complete dates; 3 year-month dates | **Required** — retain source precision; no day imputation. |
| Key integrity | No duplicate `USUBJID/PRSEQ`; subject mapping complete | **PASS** for staging readiness. |
| ADSL linkage | 65/65 PR subjects link to real MP ITT ADSL | **PASS** for linkage readiness. |
| Endpoint qualification | ED-02 CM+PR union and intent rule adopted | **AUTHORIZED** for Phase 2 implementation; post-rerun event consumption remains subject to reconciliation and adjudication controls. |

## 5. Adopted staging/source specification — Phase 2 implementation

With ED-02 adopted, the staging layer shall:

1. Create `01_source_data/real_sdtm/staging/pr.rds` from the raw PR domain using the existing uppercase-domain ingestion convention.
2. Preserve all 151 rows and all source variables; do not filter to radiotherapy at ingestion.
3. Preserve `PRDTC` exactly and derive a separate complete-date field only for complete ISO values.
4. Carry explicit date precision/status flags for partial dates; do not impute a day.
5. Retain `USUBJID`, `PRSEQ`, and `SUBJID` as source lineage keys.
6. Construct the downstream candidate set from the union of direct-intent CM and PR records; require a radiation concept plus explicit `PALLIATIVE` or `ANTALGIC` source text.
7. Do not auto-classify generic radiotherapy, prior-radiation categories, radiopharmaceuticals or substring false positives as palliative pain events.
8. Collapse only exact subject/date duplicates automatically, retaining both source records and provenance. Do not silently merge non-exact dates.
9. Apply the author-adopted date and cancer-related qualification rules only in the downstream endpoint derivation layer.
10. Add SAS/R regression fixtures for duplicate keys, partial/missing dates, same-day cross-domain records, non-exact records, post-randomization timing, generic radiation and false-positive text.

This is a proposed technical staging design, not an independently or medically approved clinical derivation.

## Phase 2 implementation closure addendum — 2026-08-04

Antony Bevan adopted ED-02 as written. The staging and endpoint layers now implement the CM+PR direct-intent union, exact duplicate collapse with source provenance, complete-date hierarchy, partial-date exclusion from the primary exact-date event pool, and diary-only/RT-only/date-bound supporting lineages. This closes the staging-readiness action for the controlled Path A demonstration; it does not substitute for independent medical adjudication or sponsor approval.

## 6. Release and data-integrity boundary

This audit did not modify or regenerate:

- `ADTTE`, `ADRS`, or any other ADaM dataset;
- current PFS event labels, censoring, or summaries;
- controlled TFLs, metadata, eCTD-style package, or release seals;
- the Path A product claim.

The raw patient-level PR file remains outside git under the repository data-rights policy. The accompanying profile is aggregate-only.

## 7. Exit criteria for ED-02 implementation

Before CM or PR is consumed by a regenerated controlled endpoint output, the implementation must demonstrate:

- author-adopted CM+PR union and exact-duplicate precedence;
- author-adopted treatment-intent classification rule;
- author-adopted date precision and window handling;
- accountable-author identity, decision date, and single-author limitation acknowledgement;
- a planned SAS/R reconciliation and subject-level impact report.
