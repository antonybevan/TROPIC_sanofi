# F-042 provisional implementation note

**Version:** 0.1.0
**Date:** 2026-08-03
**Execution status:** **PROVISIONAL PRE-ADOPTION ARTIFACT — ED-01–ED-07 ADOPTED 2026-08-04**
**Production status:** **NO PRODUCTION CONSUMPTION; SEALED PATH A OUTPUTS UNCHANGED**

> **Historical artifact — superseded 2026-08-09.** The counts and comparisons below describe
> the isolated pre-production implementation. The current governed production summary is 37
> primary subjects (36 diary-only and 1 direct-RT-only), 15 complete-date RT inventory records
> plus 1 missing/partial-date record, and 43 pain responses among 156 evaluable real-MP subjects.
> Current production evidence, not this provisional note, governs the pipeline.

## Purpose and boundary

The project author directed exploratory implementation to continue and indicated
that Phase 2 adoption was pending. The controlled decision record now records
Antony Bevan's adoption of ED-01–ED-07 as written on 2026-08-04. This note
remains a bounded, non-production artifact and does not fabricate sponsor
approval, independent review, or regulated authorization.

The implementation is isolated in
[`f042_provisional_pain_derivation.R`](../../../04_analysis_datasets/programs/r/f042_provisional_pain_derivation.R).
It is not sourced by the production DAG, does not overwrite or reseal
`04_analysis_datasets/adam/adtte_prod.xpt`, and writes only to an explicitly
supplied temporary/output directory. The controlled decision record remains
`author_adopted_phase_2_authorized`; `implementation_gate.phase_2_allowed` is
now `true`, but this isolated script is not the production ADTTE consumer.

The local output also includes the patient-level RT review file specified by the
[CM/PR adjudication worksheet specification](F042_ADJUDICATION_WORKSHEET_SPEC_2026-08-03.md)
and the subject-level current-versus-provisional comparison. Those files remain
local because patient-level source/output records are not part of the Git review
surface.

This provisional step does not change the production SAS program. A separate
SAS implementation and SAS/R reconciliation are required under the adopted
Phase 2 plan before any controlled output is regenerated.

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
- The local run produced 16 CM/PR inventory records, 15 complete-date records,
  13 adjudication records, and a one-row-per-ITT-subject impact comparison;
  generated patient-level CSVs were not committed.
- The sealed `adtte_prod.xpt` file was not modified.

## Required path to formal adoption

Before any production integration, output regeneration, release reseal, or
filing-facing claim, the adopted rule must be programmed separately in SAS and
R, reconciled at subject level, run through the full DAG and TFL/metadata
checks, reviewed in the delayed second pass, and subjected to qualified
external statistical/medical review before any regulated reuse.
