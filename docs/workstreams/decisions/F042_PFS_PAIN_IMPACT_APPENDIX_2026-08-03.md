# F-042 PFS Pain Component — Quantified Impact Appendix

**Parent record:** [`ENDPOINT_DECISION_RECORD_F042_T11_8_2026-08-03.md`](ENDPOINT_DECISION_RECORD_F042_T11_8_2026-08-03.md)<br>
**Status:** Descriptive evidence only; no clinical rule approved<br>
**Product path:** Path A controlled non-submission demonstration<br>
**Baseline:** real MP ADTTE from the final 34-stage ODA run

## 1. What is being measured

This appendix quantifies the records that could be affected by the unresolved SAP requirement that PFS pain progression have supporting disease evidence and account for palliative radiotherapy. It does not decide which records qualify.

The counts are from the real MP arm. The reconstructed CbzP ADTTE is a separate synthetic demonstration layer and does not contain the same component-level provenance. No comparative inference is made here.

## 2. Current baseline counts

| Measure | Count | Denominator / note |
|---|---:|---|
| PFS ITT records | 371 | One record per real MP ITT subject |
| PFS event records | 327 | `CNSR=0` |
| Disease-progression component events | 282 | Current `EVNTDESC='DISEASE PROGRESSION'` |
| Pain-progression candidate events | 37 | Current `EVNTDESC='PAIN PROGRESSION'`; not SAP-qualified |
| Death component events | 8 | Current `EVNTDESC='DEATH'` |
| Censored records | 44 | `CNSR=1` |
| Pain candidates as share of PFS ITT | 10.0% | 37 / 371 |
| Pain candidates as share of PFS events | 11.3% | 37 / 327 |

The 37 pain-labelled candidate events occur between 2007-01-17 and 2008-12-03 in the source-date representation. They are all real MP records.

## 3. Palliative-radiotherapy source evidence

The raw PR source file is `01_source_data/real_sdtm/pr.sas7bdat`. It is not currently staged into the governed handoff and therefore is not used by the current ADTTE derivation.

| PR evidence | Count | Interpretation |
|---|---:|---|
| Radiation-related PR rows | 11 | `PRTRT` terms containing radiotherapy/radiation |
| Subjects with radiation-related PR rows | 9 | Subject-level distinct count |
| Pain-event subjects with any radiation-related PR row | 1 | Subject overlap only; does not establish qualification |
| Radiation PR rows on or before the current pain event | 0 | Exact date-only comparison |
| Radiation PR rows after the overlapping pain event | 3 | All three are 23–25 days after that event |

The date-only comparison is a descriptive screen. It cannot answer whether a later palliative-radiotherapy record should modify a prior pain progression, because the SAP window, intent rule, and event precedence are not approved.

## 4. Bounded event-count scenarios

The following range is a programming impact bound, not a statistical result:

| Scenario | Pain candidates retained as PFS events | Total PFS events | Required interpretation |
|---|---:|---:|---|
| Current Path A label | 37 | 327 | Disclosed component labels; not SAP-complete |
| Conservative all-excluded bound | 0 | 290 | 282 disease + 8 death; requires approved exclusion rule |
| Partial qualification | `k`, where 0 ≤ `k` ≤ 37 | `290 + k` | Requires subject-level qualification and source traceability |

Any change to the retained set requires regeneration of PFS `ADT`, `AVAL`, `CNSR`, event descriptions, KM summaries, medians, hazard ratios, risk tables, figures, and all dependent reviewer metadata. Counts alone cannot predict the direction or size of a treatment-effect change.

## 5. Decision-to-impact matrix

| Decision | Potentially changed artifacts | Minimum evidence required |
|---|---|---|
| ED-01 supporting disease evidence | ADTTE PFS event/censor fields; PFS TFLs; KM/HR outputs; ADRG/traceability | Approved source set, hierarchy, window, and subject-level adjudication |
| ED-02 PR source/precedence | SDTM staging, ADTTE PFS/TTPAIN, source traceability, Define methods | Staged PR profile, CM handling, date precision and intent rule |
| ED-03 RT-only sensitivity | Sensitivity ADTTE/TFL, analysis results, reviewer narrative | Approved sensitivity estimand and output disposition |
| ED-04 T-11-8 collision | TFL catalog, physical table IDs, ARM/ARS, Define, package index, reviewer guides | Approved TTPAIN ID and approved response extension ID or SAP amendment |
| ED-05 TTUMOR population | TTUMOR dens, shell wording, estimand and metadata | Explicit SAP population interpretation |
| ED-06 time origins | `STARTDT`, `AVAL`, ADRG, traceability, Define methods | Parameter-level origin approval and synchronized text |

## 6. Phase 1 preservation statement

This appendix was prepared without changing ADTTE, ADRS, TFL, metadata, package, release-manifest, or machine-gate outputs. It does not close F-042, approve T-11-8, or expand the Path A product claim.

## 7. Phase 2 acceptance criteria

The next implementation may begin only when the parent record contains the required approvals. Its evidence package must include:

- SAS and R source/staging changes with a governed PR profile.
- Subject-level before/after disposition of every affected PFS candidate.
- Primary and approved sensitivity endpoint counts and summaries.
- Exact SAS/R reconciliation and scoped admiral reconciliation where applicable.
- Updated TFL/metadata/package crosswalk with no stale or colliding IDs.
- Full 34-stage real-SAS rerun and release verification before reseal.
