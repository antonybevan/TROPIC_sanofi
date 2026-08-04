# Section 2 — Populations, endpoints, SAP/config/TFL control audit

**Review date:** 2026-08-03  
**Product claim:** Path A controlled non-submission demonstration  
**Audit baseline:** `codex/submission-pipeline-rc` after commits `458060c` and `8673cfa`  
**SAP reviewed:** `02_specifications/sap/TROPIC_SAP_v4.0_industry_grade.docx`  
**Rendered SAP QA:** 22 pages rendered with the documents workflow; pages 1–22 visually reviewed with no clipping, overlap, broken table, or unreadable continuation detected.

## Approval-preparation addendum

The later protocol/publication/source-to-code review found that the original handoff understated the required correction. The accountable-author decision-ready [`F-042 Endpoint Approval Specification`](../../../docs/workstreams/decisions/F042_ENDPOINT_APPROVAL_SPEC_2026-08-03.md) supersedes this audit's former recommended dispositions for S2-01, S2-02 and S2-04:

- restore the existing SAP-native `T-11-3` PSA response, `T-11-4` ORR, `T-11-5` pain response and `T-11-8` TTPAIN mappings rather than assigning the primary response results to a new extension;
- use ITT as primary TTUMOR, with measurable disease as support rather than primary denominator; and
- replace the current pain algorithm, which uses non-conforming thresholds, AS summary and confirmation logic.

The historical observations and counts below remain evidence of the sealed Path A state; they are not the recommended signed endpoint rules.

## Decision

**AMBER — PASS for the current Path A implementation handoff, with two SAP/TFL alignment items requiring explicit disposition before any filing-facing or SAP-complete claim.**

The population derivations and the controlled response denominator now connect correctly to the live MP and reconstructed CbzP data. The controlled TFL index also agrees on the corrected `T-11-6 = TTUMOR` and `T-11-7 = TTPSA` identifiers. This does not close the SAP catalog ambiguity: the physical `T-11-8` block is a response summary, while SAP v4.0 Appendix D Table 22 defines `T-11-8` as time to pain progression. That is a control-surface mismatch, not a cosmetic title issue.

## 1. SAP rules read and used for this audit

The rendered and text-extracted SAP supplied these controlling rules:

| SAP location | Rule used in this audit |
|---|---|
| Table 11 / §5 | ITT is all randomized subjects; safety is all-treated; ORR uses measurable disease; PSA response requires baseline PSA >=20 ug/L plus evaluable confirmation. |
| §9 / Table 13 | OS is randomization-to-death; alive subjects are censored at last known alive/cut-off; primary estimator is KM plus stratified log-rank/Cox. |
| §10.1 / Table 13 | PFS is the earliest valid PSA, tumour, pain-with-disease-evidence, or death event with NACT censoring. |
| §10.2 / Appendix B | PSA response is a confirmed >=50% decline with a repeat at least three weeks later; progression rules differ for responders and non-responders. |
| §10.3 / Table 16 | RECIST v1.0 governs ORR and tumour progression; confirmation is at least four weeks. |
| §10.4 / Table 16 | Pain response requires diary evaluability; pain progression is from baseline/reference and includes palliative radiotherapy. |
| Table 22 / Appendix D | `T-11-6` is TTUMOR, `T-11-7` is TTPSA, and `T-11-8` is TTPAIN. |
| §17 | The SAP catalog is controlled; produced output without an approved shell/catalog mapping is not release-ready. |

## 2. Independent live-data recheck

The check used the current local XPTs, independent of the narrative documents. Patient-level XPTs remain ignored/untracked by policy.

| Check | Current result | Interpretation |
|---|---:|---|
| Real MP ADSL | 371 subjects; `TRT01P=MP` for all | Correct DM-derived real layer. |
| Synthetic CbzP ADSL | 378 subjects; `TRT01P=CbzP` for all | Reconstructed demonstration layer only. |
| Combined display cohort | 749 (`371 + 378`) | Not protocol ITT 755; F-012 remains accepted and disclosed. |
| Safety population | MP 371; CbzP 371 | Correct all-treated denominator; seven synthetic CbzP subjects are `SAFFL=N`. |
| Measurable disease | MP 203; CbzP 179 | Current arm-specific denominators; the old WS-2 statement “N=203” was MP-only and incomplete. |
| Baseline PSA >=20 | MP 330; CbzP 361 | SAP PSA eligibility denominator. |
| Eligible `PSARESP` rows | 691 total: MP 330, CbzP 361; no duplicate subjects | Eligible set is unique and complete for the current ADaM layer. |
| PSA responders | MP 61/330 (18.5%); CbzP 145/361 (40.2%) | F-011 implementation is resolved and independently reproduced. |
| ORR TFL denominator | MP 203, CbzP 179; missing `OBJRESP` becomes non-response | Correct MEAS left-join; do not use the BOR `OBJRESP` spine as denominator. |
| ADTTE TTUMOR | MP 203, CbzP 179 | Endpoint-specific measurable-disease implementation; see SAP clarification finding below. |
| ADTTE TTPSA | MP 371, CbzP 378 | ITT demonstration cohort. |
| ADTTE TTPAIN | MP 371, CbzP 378 | ADTTE parameter exists, but no separate controlled TTPAIN TFL is produced. |

## 3. Controlled output crosswalk

| Controlled output | Population actually used | Endpoint evidence | Status |
|---|---|---|---|
| `F-11-1` | ITT-shaped demonstration cohort; real MP plus synthetic CbzP | ADTTE `OS`; physical KM figure and SAS companion | PASS with synthetic/non-confirmatory limitation. |
| `F-11-2` | ITT-shaped demonstration cohort; real MP plus synthetic CbzP | ADTTE `PFS`; physical KM figure and SAS companion | PASS with synthetic/non-confirmatory limitation. |
| `F-12-1` | OS subgroup cohort with pooled ECOG 0–1 vs 2 and MEASDISF | ADTTE `OS` + ADSL covariates | PASS; F-030 resolved. |
| `F-13-1` | Baseline PSA >=20 subset | ADLB PSA + ADSL | PASS; eligibility matches the PSA response set. |
| `F-14-1`, `T-17-*`, `F-17-1` | Safety/all-treated where applicable | ADEX/ADLB/ADTTE | PASS for controlled demonstration scope; synthetic safety is non-confirmatory. |
| `T-11-6` | MEASDISF: MP 203, CbzP 179 | ADTTE `TTUMOR`; physical block says TTUMOR | PASS for implementation; SAP Table 22 population wording needs clarification. |
| `T-11-7` | ITT-shaped: MP 371, CbzP 378 | ADTTE `TTPSA`; physical block says TTPSA | PASS; F-031 identifier reversal is closed. |
| `T-11-8` | PSA eligible MP 330/CbzP 361 and MEAS ORR MP 203/CbzP 179 | Physical block is best clinical response (PSA + ORR) | **OPEN SAP-ID mismatch**: SAP Table 22 calls this ID TTPAIN. |
| `T-11-8b` | `OBJRESP` response-evaluable spine: MP 351, CbzP 378 | ORR sensitivity addendum | PASS as an explicitly labelled extension; not a SAP TTPAIN replacement. |
| `T-20-1/2` | `SAFFL=Y`, N=371 per arm | ADAE TEAE summaries | PASS with synthetic dictionary limitation. |
| `T-21-1/2` | Safety denominator; shift-evaluable records shown separately | ADLB grade shifts | PASS with shift-evaluable N footnotes. |

## 4. Findings requiring disposition

### S2-01 — SAP TFL identifier/endpoint collision (Major control risk)

**Evidence:** SAP Appendix D/Table 22 defines `T-11-8` as “Time to Pain Progression.” The physical output, `config/tfl_output_catalog.yaml`, `docs/TFL_OUTPUT_INDEX.md`, CTQ register, and traceability matrix currently treat `T-11-8` as a best clinical response table containing PSA response and ORR. `ADTTE.TTPAIN` exists, but no separate controlled TTPAIN table is indexed.

**Why it matters:** A reviewer can follow the ID from SAP to the wrong endpoint and believe TTPAIN evidence was produced when it was not, or believe the response table is a SAP-approved TTPAIN output. This violates SAP §17's shell/catalog rule even though the text block itself is numerically internally consistent.

**Required controlled decision before a filing-facing claim:** choose one and record it in a signed/amended analysis specification:

1. Implement and index the SAP TTPAIN table as `T-11-8`, and move the current response summary to an explicitly approved extension ID; or
2. Approve an SAP/catalog amendment that reassigns the response summary and separately dispositions TTPAIN as deferred.

Until that decision is recorded, the current response block must be described as a Path A demonstration extension, not as the SAP T-11-8 TTPAIN deliverable.

### S2-02 — TTUMOR population wording is internally inconsistent (Major specification risk)

**Evidence:** SAP Table 22 lists `T-11-6` population as ITT, while SAP Table 11, Table 13, and Table 16 describe tumour response/progression as measurable-disease or endpoint-specific evaluability. The production and validation ADTTE tracks consistently implement `TTUMOR` on `ITTFL='Y' & MEASDISF='Y'`, yielding MP 203 and CbzP 179.

**Decision for Path A:** retain the current endpoint-specific measurable implementation and disclose it. Do not relabel the 203/179 output as all-ITT. A sponsor-facing SAP amendment must resolve whether T-11-6 is ITT with missing tumour assessments censored, or a measurable-disease analysis set.

### S2-03 — Time-origin language is not explicit and reviewer guides conflict (Moderate specification risk)

**Evidence:** The live SAS/R ADTTE tracks use `RANDDT` for OS, PFS, TTPAIN, TTPSA, and TTUMOR, with `TRTSDT` for TTSAE. The traceability matrix describes the efficacy endpoints as randomization-anchored, while a current ADRG passage describes TTPSA/TTUMOR as first-dose anchored. SAP v4.0 specifies populations and endpoint events but does not state the start date for these secondary TTE parameters with sufficient precision.

**Decision for Path A:** treat the reconciled SAS/R code and ADTTE `STARTDT` values as the current implementation truth; correct the reviewer-guide contradiction in the next writing pass. A filing SAP must state the origin per parameter before rerun.

### S2-04 — Pain progression algorithm has deferred-specification elements (Moderate; Section 3 handoff)

The current dual-language TTPAIN derivation enforces five-of-seven diary evaluability and confirmation, but the SAP also mentions baseline/reference eligibility and palliative radiotherapy. These rules are not represented in a controlled TFL in the current Path A catalog. Section 3 must verify source availability and either implement, explicitly scope out, or amend the endpoint specification.

## 5. Control-surface corrections made with this review

- Corrected WS-2 date, arm-specific MEAS denominators, PSA eligibility counts, and `T-11-6`/`T-11-7` mappings.
- Removed the stale “F-011 deferred” wording from the current WS-2 control pack; F-011 is resolved for the current response set.
- Added an explicit SAP/TFL ID collision note so the mismatch cannot be mistaken for a closed mapping.
- Confirmed G02 is runtime stage-gated; its current check is a structural lock, not a substitute for this semantic audit.

## 6. Handoff

**To Section 3:** audit ADTTE/ADRS derivations against S2-02 through S2-04, including start dates, no-post-baseline censoring, diary eligibility, and palliative-RT source availability.  
**To Section 4:** reconcile metadata/ARM/TFL catalog wording after the S2-01 decision; do not regenerate a “SAP-complete” TFL index before that decision.  
**Release posture:** Path A controlled demonstration may continue with the explicit limitations above. Submission-readiness or SAP-complete language remains blocked.

## Phase 2 closure addendum — 2026-08-04

The historical findings above are retained as the pre-adoption baseline. Antony Bevan adopted ED-01–ED-07 on 2026-08-04. The controlled implementation now uses ITT as the TTUMOR primary population (with measurable disease supportive), stages SV/PR alongside CM/PN, applies the adopted component-specific pain and CM+PR qualification rules, and restores the SAP-native `T-11-3` PSA response, `T-11-4` ORR, `T-11-5` pain response, `T-11-6` TTUMOR, `T-11-7` TTPSA and `T-11-8` TTPAIN mappings. The final full-DAG rerun and release reseal remain the evidence gate; this addendum does not represent independent, sponsor, medical or regulated approval.

## Section 3 correction addendum — 2026-08-03

The Section 2 live-data snapshot counted one MP subject whose ADSL baseline PSA (`PSABL=110`) was a controlled fallback (`PSABLIF='Y'`) as PSA-eligible. Section 3 rechecked the source baseline and corrected the governed response eligibility rule to exclude fallback values while retaining synthetic comparator rows with no `PSABLIF` field. The corrected current denominator is **690 unique subjects: MP 329 and CbzP 361; responders remain MP 61 and CbzP 145**. This supersedes the Section 2 snapshot values 691 / MP 330 for current output generation; the original values remain above as historical audit evidence rather than being silently overwritten.
