# F-042 Delayed Second-Pass Review Record

**Record ID:** `F042-SECOND-PASS-2026-08-04`
**Product path:** Path A — controlled non-submission demonstration
**Accountable author:** Antony Bevan
**Review date:** 2026-08-04
**Status:** **HISTORICAL PASS; NOT SUFFICIENT AS SOLE APPROVAL EVIDENCE — see statistical governance assessment**

> **2026-08-09 supersession note.** This frozen pass predates the no-floor ADTTE contract and
> the current F-042 counts. Its accepted time-origin warning exception is no longer active:
> missing/pre-origin dates now fail the build. Current F-042 evidence is 37 primary subjects
> (36 diary-only, 1 direct-RT-only) and 43/156 pain responses. A new full-DAG run is required
> for the changed source tree; this record cannot supply it.

## Purpose and independence boundary

This is a deliberately delayed, checklist-based second pass after implementation of
the author-adopted ED-01–ED-07 decision set. It challenges the implementation against
the controlled specification and the known findings before the final release seal.
It is not an independent human QC review: the project has one programmer of record,
and no sponsor, medical, statistical, Part 11 or regulated approval is represented.

## Frozen review basis

| Item | Controlled basis |
|---|---|
| Decision authority | `docs/workstreams/decisions/ENDPOINT_DECISION_RECORD_F042_T11_8_2026-08-03.md` |
| Executable specification | `docs/workstreams/decisions/F042_ENDPOINT_APPROVAL_SPEC_2026-08-03.md` |
| Source qualification | `docs/workstreams/decisions/F042_PR_SOURCE_QUALIFICATION_AUDIT_2026-08-03.md` |
| Implementation | Separate SAS `F042_phase2_pain_derivation.sas` and R `f042_provisional_pain_derivation.R` tracks |
| Controlled output mapping | `config/tfl_output_catalog.yaml`, `platform/build_tfl_output_index.py`, T-11 efficacy table |
| Review boundary | Path A non-submission only; raw patient-level source remains outside Git |

## Second-pass checklist

| Check | Expected challenge | Status |
|---|---|---|
| Author adoption | ED-01–ED-07 are adopted as written and single-author limitation is explicit | PASS — record and approval specification |
| Staging | SV and full PR are staged without patient-level Git artifacts | PASS — R/SAS staging regression |
| Date hierarchy | Complete SV visit dates precede controlled PN fallback; partial RT dates stay out of primary exact-date pool | PASS — implementation review |
| Pain algorithm | Component-specific summaries, baseline/reference rules, same-component confirmation, no terminal exception | PASS — R fixtures and SAS module review |
| CM+PR qualification | Direct-intent CM and PR union, exact duplicate provenance, generic radiation excluded | PASS — aggregate source evidence |
| Sensitivities | Primary diary/RT, diary-only, RT-only and date-bound lineages are retained | PASS — F-042 summary outputs |
| TTUMOR population | ITT primary; measurable disease supportive only | PASS — reconstruction and ADTTE code review |
| SAP-native mapping | T-11-3 PSA, T-11-4 ORR, T-11-5 pain response, T-11-6 TTUMOR, T-11-7 TTPSA, T-11-8 TTPAIN | PASS — catalog, physical block and guide review |
| Dual-language challenge | R/SAS exact parity and scoped admiral checks remain green | PASS — full run; ADTTE/ADSL/OS/PFS controls passed |
| Log challenge | Missing arithmetic values are guarded; only reviewed F-017 time-origin warnings remain | PASS — current log gate |
| Final execution | Full 34-stage real-SAS DAG, health `full_dag`, release manifest `PASS`, clean tree | PASS — 34/34, ODA, bridge/recon/package/log gates green; release manifest and CI verification passed |

## Post-review exception

The later [Path A Statistical Governance Assessment](PATH_A_STATISTICAL_GOVERNANCE_ASSESSMENT_2026-08-04.md)
identified `GOV-STAT-01`: the SAS T-11-5 branch required a confirming visit at least
21 days later but tested response only at the initial visit. That SAS branch produced
65 responder subjects versus the correct R-derived 43, while the displayed TFL
happened to use the correct R value. The prior dual-language checklist assertion was
therefore too broad: ADTTE parity was valid, but T-11-5 subject-level response parity
had not been tested.

The SAS rule and release gate have been corrected. This record remains the historical
delayed-pass evidence and must be read with the governance assessment and the current
`endpoint_controls.F042_PAIN_RESPONSE` result.

## Disposition

At the time of this pass, no implementation defect was identified and the complete
real-SAS DAG passed 34/34 stages on ODA (SAS 9.04.01M8P022223). `GOV-STAT-01`
subsequently showed that the review did not cover the independent T-11-5 subject set.
This record cannot authorize release of a changed source tree. Current Path A
promotion is governed by the statistical-governance assessment and its mandatory
real-SAS endpoint-level reconciliation condition.

**Author acknowledgement:** Antony Bevan — delayed second-pass review conducted under
the disclosed single-author limitation; this acknowledgement is a project control
record, not an electronic signature or regulated approval.
