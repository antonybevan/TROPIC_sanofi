# F-042 provisional implementation note

**Version:** 0.1.0
**Date:** 2026-08-03
**Execution status:** **PROVISIONAL AUTHOR-DIRECTED — FORMAL SIGN-OFF PENDING**
**Production status:** **NO PRODUCTION CONSUMPTION; SEALED PATH A OUTPUTS UNCHANGED**

## Purpose and boundary

The project author directed exploratory implementation to continue and indicated
that the formal author signature will be supplied later. This note records that
bounded instruction without fabricating an identity, signature, date, sponsor
approval, independent review, or regulated authorization.

The implementation is isolated in
[`f042_provisional_pain_derivation.R`](../../../04_analysis_datasets/programs/r/f042_provisional_pain_derivation.R).
It is not sourced by the production DAG, does not overwrite or reseal
`04_analysis_datasets/adam/adtte_prod.xpt`, and writes only to an explicitly
supplied temporary/output directory. The controlled decision record remains
`author_decision_ready_pending_signoff`; `implementation_gate.phase_2_allowed`
remains `false`.

This provisional step does not change the production SAS program. A separate
SAS implementation and SAS/R reconciliation are required only after the signed
decision record authorizes controlled integration.

This is an exploratory programming artifact for author review. It is not an
approved endpoint derivation, a filing-ready result, a substitute for a signed
decision record, or evidence of independent statistical/medical QC.

## Provisional rule implementation

The R functions implement the currently proposed ED-01/ED-02/ED-07 rules while
preserving source lineage:

| Area | Provisional behavior |
|---|---|
| Baseline | Seven calendar days ending on `TRTSDT`; component-specific `PAININT` median and `ANSCORE` mean; at least five valid distinct dates; no missing-to-zero imputation. |
| Diary trigger | `PAININT` increase `>=1`; `ANSCORE` increase `>=25%` only when the positive baseline is evaluable. |
| Confirmation | Same component at the immediately next scheduled evaluation, at least 21 days later; no terminal-trigger exception and no bridge over a missing/non-evaluable scheduled visit. |
| Visit dates | `SVSTDTC` first; maximum observed PN date only as an explicitly labelled fallback; unscheduled visit `99` excluded from the primary schedule. |
| Disease support | Post-randomization ADRS `OVRLRESP=PD` or bounded DS progression-week evidence no later than the confirming visit. |
| Radiotherapy | Full CM+PR inventory with explicit `PALLIATIVE`/`ANTALGIC` and a radiation concept. Generic, prior/history, and radiopharmaceutical-classified records are retained as adjudication lineage and are not automatic events. |

For CM, the explicit-intent text is evaluated from the reported `CMTRT` field
per the source qualification audit; `CMINDC` is retained as context but cannot
convert generic `RADIOTHERAPY` into an automatic event.

The CM source contains 13 direct-intent inventory records across 10 subjects
(12 complete start dates and one missing start date), and the PR source contains
three complete-date records for one different subject. In this dataset, the 12
complete-date CM records have a radiopharmaceutical controlled classification
despite external-beam-like free text; the missing-date CM record cannot be an
event. The provisional code therefore retains all 16 inventory records (15
complete-date records), automatically qualifies only the three PR records, and
flags all 13 CM records for accountable-author adjudication rather than
silently promoting or discarding them.

## Exploratory data impact (not an analysis result)

The run was performed against the current local ADaM/SDTM inputs and written to
a temporary directory. The output summary was:

| Measure | Count |
|---|---:|
| ITT subjects | 371 |
| Confirmed diary events before disease support | 157 |
| Diary events with qualifying support | 59 |
| CM+PR RT inventory records | 16 |
| CM+PR complete-date RT records | 15 |
| Automatically qualifying RT events | 3 |
| RT records requiring adjudication | 13 |
| Complete-date RT records requiring adjudication | 12 |
| Primary provisional event subjects (diary-or-auto-RT) | 45 |
| Current sealed TTPAIN event rows used for comparison | 75 |
| Provisional additions / removals / re-dates | 20 / 50 / 25 |

These counts are diagnostic only. They do not replace the sealed ADTTE/TFL
results and must not be copied into a submission package.

## Verification performed

- R parser check passed for the provisional program.
- Synthetic regression tests passed in
  [`test_f042_provisional_pain_derivation.R`](../../../tests/test_f042_provisional_pain_derivation.R),
  covering thresholds, summaries, duplicates/discordance, confirmation timing,
  missing-visit bridging, terminal triggers, unscheduled visits, CM+PR flags,
  and post-randomization evidence.
- The sealed `adtte_prod.xpt` file was not modified.

## Required path to formal adoption

Before any production integration, output regeneration, release reseal, or
filing-facing claim, the author must complete the controlled decision record
and sign/date the ED-01–ED-07 disposition. The subsequent controlled work must
then program the adopted rule separately in SAS and R, reconcile subject-level
lineage, run the full DAG and TFL/metadata checks, complete the delayed
second-pass review, and obtain qualified external statistical/medical review
before any regulated reuse.
