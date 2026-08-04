# F-042 CM/PR adjudication worksheet specification

**Version:** 0.1.0
**Status:** **PROVISIONAL REVIEW TOOL — NOT A CLINICAL DECISION OR APPROVAL**
**Parent record:** [`EDR-F042-T11-8-2026-08-03`](ENDPOINT_DECISION_RECORD_F042_T11_8_2026-08-03.md)
**Generator:** [`f042_provisional_pain_derivation.R`](../../../04_analysis_datasets/programs/r/f042_provisional_pain_derivation.R)

## Purpose and handling boundary

This worksheet defines the minimum evidence needed for the accountable author to
review direct-intent CM/PR radiotherapy records under ED-02. It is deliberately
separate from the production ADTTE/TTPAIN/PFS programs. The generator writes the
patient-level CSV only to a caller-supplied local output directory; the CSV is
not committed to Git, included in the release seal, or copied into the
submission package.

The worksheet records a proposed classification and the evidence needed to
accept, reject, or defer it. It does not pre-populate a clinical decision and
does not replace the signed parent decision record.

## Current source inventory

The current local run contains:

| Inventory | Records | Complete start dates | Current provisional disposition |
|---|---:|---:|---|
| CM direct-intent records | 13 | 12 | Adjudication required; 12 complete records carry a radiopharmaceutical controlled classification and one record has a missing start date. |
| PR direct-intent records | 3 | 3 | Automatically eligible under the provisional text/date rule, subject to author adoption and downstream cancer-related qualification. |
| CM+PR records retained in the worksheet | 16 | 15 | All records retained with source provenance; only complete, post-randomization dates can become events. |

For CM, direct intent is screened from `CMTRT` text containing a radiation
concept plus `PALLIATIVE` or `ANTALGIC`. `CMINDC` is retained as context but
cannot promote generic `RADIOTHERAPY` into an automatic event. Radiopharmaceutical
terms in the treatment/classification concept and prior/history categories are
flagged rather than silently resolved.

## Required worksheet columns

The generated `f042_provisional_rt_adjudication_worksheet.csv` contains the
following review fields:

| Field | Required review use |
|---|---|
| `USUBJID` | Local subject key; keep outside Git and controlled review systems. |
| `source_domains`, `source_keys` | CM/PR provenance and exact source record identifiers. |
| `event_date` | Complete source start date; blank means not date-usable. |
| `treatment_text`, `intent_text`, `indication_text`, `category_text` | Source text supporting or contradicting direct local palliative intent. |
| `rt_autoqualifies` | Machine proposal only; `TRUE` is not author approval. |
| `exclusion_reasons` | Machine reason for adjudication, including radiopharmaceutical classification, prior/history category, or missing start date. |
| `source_record_count` | Number of source rows collapsed at the same subject/date. |
| `author_disposition` | To be completed: `ADOPT`, `EXCLUDE`, or `DEFER`. |
| `author_reason` | Plain-language rationale and any source clarification. |
| `author_initials`, `author_signature_ref`, `decision_date` | Controlled review evidence; blank until actually completed. |

The last five fields are review-only additions. The generator intentionally does
not fabricate them. A controlled reviewer may add them to a local copy or a
validated review system after inspecting the source record.

## Reproduction command

With the licensed local source layer available, generate the worksheet and
subject-impact files into a local directory:

```bash
run_dir=$(mktemp -d /tmp/f042_adjudication.XXXXXX)
Rscript 04_analysis_datasets/programs/r/f042_provisional_pain_derivation.R \
  "$(pwd)" "$run_dir"
```

The same directory contains `f042_provisional_subject_impact.csv`,
`f042_provisional_rt_lineage.csv`, and the aggregate
`f042_provisional_summary.csv`. The command does not modify ADTTE/TFL outputs or
the release seal.

## Decision rules for the reviewer

1. Confirm the source record and date precision from the raw CM/PR domain; do
   not infer a missing day.
2. Confirm that the treatment/procedure itself is local radiation and that the
   direct intent is palliative or antalgic.
3. Resolve the conflict between external-beam-like `CMTRT` text and a
   radiopharmaceutical `CMDECOD`/classification explicitly; do not use the
   provisional machine flag as a clinical ruling.
4. Exclude prior/history treatment unless the author documents a controlled
   replacement rule.
5. If the start date is missing or partial, retain the source lineage but do not
   assign an exact primary event date.
6. Record one disposition per collapsed subject/date record and link any
   supporting source review. Conflicting source records on the same date should
   remain visible in `source_keys`.

## Exit criteria

The worksheet is complete only when every retained CM/PR record has a controlled
author disposition, rationale, and date, and the parent decision record has the
matching adopted ED-02 election. It remains a non-production review artifact;
the regenerated SAS/R endpoint outputs must reconcile the same subject/date
lineage independently before any record is treated as a controlled event.
