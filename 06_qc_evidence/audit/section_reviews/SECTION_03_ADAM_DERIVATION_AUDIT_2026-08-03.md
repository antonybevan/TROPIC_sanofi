# Section 3 — ADaM derivation and endpoint validation audit

**Review date:** 2026-08-03
**Product claim:** Path A controlled non-submission demonstration
**Authorities:** SAP v4.0 (`02_specifications/sap/TROPIC_SAP_v4.0_industry_grade.docx`), ADSL/ADRS specifications, `config/study_config.yaml`
**Programs reviewed:** `A_adtte_generation.sas`, `v_adtte_validation.R`, `admiral_adtte.R`, `tfl_generation.R`
**Evidence run:** real-SAS ODA DAG, 34/34 stages PASS, final run after the corrections described below

> **Historical baseline notice (2026-08-05):** This dated review preserves the pre-adoption observations and decisions for auditability. The Phase 2 closure addendum below controls the current Path A state: ED-01–ED-07 were adopted, implemented, reconciled, resealed, and CI-verified. External qualified statistical/medical review remains required before any regulated or filing-facing use.

## Approval-preparation addendum

The later protocol/corrected-publication comparison established that the pain implementation is not merely missing supporting-disease and PR handling. It also uses median rather than mean AS, `PPI >=2` rather than `>=1`, absolute `AS >=10` rather than `>=25%` from baseline, combined-component confirmation, minimum diary date and a terminal single-trigger exception. These reproducible rules are non-conforming and must be replaced after authorization.

Direct-intent source review also found 13 palliative/antalgic CM RT rows across 10 subjects and 3 direct-intent PR rows for 1 different subject, so PR-only precedence is not acceptable. The accountable-author decision-ready [`F-042 Endpoint Approval Specification`](../../../docs/workstreams/decisions/F042_ENDPOINT_APPROVAL_SPEC_2026-08-03.md) supersedes the original S3-04 implementation handoff while preserving the sealed counts below as historical evidence.

## Decision

**AMBER — computational ADTTE handoff PASS; filing-facing endpoint interpretation remains blocked.**

The production SAS and validation R ADTTE tracks now agree on 2,058 records, and the scoped admiral OS/PFS track reconciles at zero cell differences. The three concrete derivation defects found during this section were corrected and regenerated through the full real-SAS DAG. A separate scientific residual remains: SAP v4.0 requires pain progression in PFS to have supporting disease evidence and to account for palliative radiotherapy, but the current source/staging layer does not yet provide an approved qualification rule or PR-domain handoff. That residual is recorded here rather than treated as closed by numerical parity.

## 1. Rules audited

| SAP rule | Control checked |
|---|---|
| §10.1 / Table 13 | PFS is the earliest valid PSA, RECIST tumour, pain-with-supporting-disease-evidence, or death event; NACT before progression censors at `NACTDT-1`; no post-baseline assessment censors at randomization. |
| §10.2 / Table 12 | PSA response requires observed baseline PSA >=20 ug/L and an evaluable confirmed response record. |
| §10.3 / Table 16 | TTUMOR is a distinct RECIST endpoint and uses the measurable-disease population in the current Path A implementation. |
| §10.4 / Table 16 | Pain uses five-of-seven diary evaluability, confirmation, baseline/reference progression, and palliative-radiotherapy handling. |
| §17 | Event/censor dates and endpoint source must remain traceable through ADTTE and the reviewer package. |

## 2. Independent live-data results

| Check | Result | Interpretation |
|---|---:|---|
| ADTTE production vs validation | 2,058 vs 2,058; exact row/parameter shape | SAS/R output contract is aligned after rerun. |
| ADTTE parameter dens | OS/PFS/TTPAIN/TTPSA/TTSAE = 371 each; TTUMOR = 203 | Population contracts are retained. |
| PFS events | 319 non-pain component labels, 37 pain component labels, 8 deaths | The existing `EVNTDESC` field now exposes the earliest composite component. |
| PFS censoring | 39 NACT, 4 last evaluable assessment, 1 no post-baseline assessment | The SAP no-post-baseline branch is now explicit. |
| TTUMOR | 185 events, 14 last RECIST assessment censors, 4 no post-baseline censors | Death milestones are excluded from the censor pool; no TTUMOR censor equals `DTHDT`. |
| TTPSA | 265 events, 106 last PSA assessment censors | Randomization origin is retained. |
| TTPAIN | 75 events, 283 last pain assessment censors, 13 no pain assessment | Five-of-seven diary processing is reproducible; RT qualification remains open. |
| PSA eligibility | MP 329, CbzP 361; responders MP 61 and CbzP 145; 690 unique eligible subjects | ADSL fallback baseline (`PSABLIF='Y'`) is excluded; synthetic rows without the flag remain eligible. |

### Corrected PFS censor records

The five records previously labelled as last-evaluable censors are now governed as follows:

| USUBJID | Correct censor date | Branch |
|---|---|---|
| `006193-038-002-202` | 2007-11-29 | No post-baseline assessment → randomization |
| `006193-058-002-002` | 2008-01-23 | Last valid PSA/assessment |
| `006193-058-002-103` | 2009-08-05 | Last valid PSA/assessment |
| `006193-058-002-502` | 2008-09-15 | Last valid PSA/assessment |
| `006193-264-001-701` | 2009-08-18 | Last valid PSA/assessment |

### Corrected PSA eligibility record

`006193-332-000-901` has `PSABL=110` with `PSABLIF='Y'`. It is excluded from the observed-baseline PSA response denominator. This changes the MP denominator from 330 to 329; the responder count remains 61.

## 3. Findings and dispositions

### S3-01 — TTUMOR death milestone used as a censor date (Major) — CORRECTED

The former censor pool selected every `ADRS.OVRLRESP` date, including the `AVALC='DEATH'` milestone generated from DS. An independent pre-correction check found five MP TTUMOR censor records whose `ADT` equalled `DTHDT`. SAS and R now restrict the censor pool to post-randomization RECIST values (`CR`, `PR`, `SD`, `PD`), and TTUMOR contains zero censor records dated on death.

**Evidence:** `A_adtte_generation.sas`, `v_adtte_validation.R`, final `adtte_prod.xpt`/`adtte_v.xpt`, and Stage 18 admiral reconciliation.

### S3-02 — PFS last-evaluable/no-post-baseline branch (Major) — CORRECTED

The former no-event branch used `LSTALVDT` while labelling the record “LAST EVALUABLE TUMOR ASSESSMENT.” The corrected implementation builds one governed date from valid post-randomization RECIST, PSA, and evaluable pain visits. It uses the latest assessment capped at the cutoff, or `RANDDT` with `CNSDTDSC='NO POST-BASELINE ASSESSMENT'` when no assessment exists. NACT remains the higher-priority censoring branch.

**Evidence:** exact SAS/R parity; five-record date table above; Stage 14 real-SAS production and Stage 18 admiral reconciliation PASS.

### S3-03 — Imputed baseline PSA included in response denominator (Major) — CORRECTED

ADSL carries a controlled fallback value for one missing source baseline PSA. The TFL, regression contract, WS-2 control table, F-011 memo, ADRG, and G02 semantic gate now require an observed baseline (`PSABLIF != 'Y'`; synthetic rows with no flag are treated as observed). Current eligible counts are MP 329 and CbzP 361, with 61 and 145 responders respectively.

**Evidence:** `tfl_generation.R`, `tests/test_tfl_population_contract.R`, `SECTION_02_POPULATIONS_ENDPOINTS_AUDIT_2026-08-03.md` correction addendum, and G02 PASS.

### S3-04 — Composite pain component and palliative-radiotherapy provenance (Major) — OPEN / ACCEPTED FOR PATH A DISCLOSURE

The current ADTTE now labels 37 PFS events as `PAIN PROGRESSION` and 282 as `DISEASE PROGRESSION`; a same-day tie is deterministically assigned to the non-pain component. A date-only screen identifies 37 pain-led candidate events with no earlier non-pain progression. SAP §10.1 requires pain progression with supporting disease evidence, and §10.4 requires palliative-radiotherapy handling. The current staging ingest does not include PR, and the source PR domain contains 11 radiation-related rows across 9 subjects (including palliative spine radiation). CM records also contain historical/prior radiation indications. The programming layer therefore cannot safely infer that every radiation record is palliative pain treatment or invent a supporting-disease rule.

**Disposition:** retain the component label and explicit residual for this Path A demonstration. Before any filing-facing claim, obtain a sponsor/statistician decision on (a) the supporting-disease qualification rule, (b) PR staging and source precedence, and (c) the palliative-RT-only sensitivity analysis. Do not describe the current PFS pain component as SAP-complete.

### S3-05 — Source date precision and flooring warnings (Moderate) — ACCEPTED / CONTROLLED

The final ODA run records 37 reviewed ADTTE time-origin exceptions (20 OS, 15 PFS, 2 TTUMOR in the independent R warning stream; the persisted log gate applies a cap of 39). Both tracks surface the subject and parameter before flooring to one day. The exception is carried as the known PDS week-offset/partial-date limitation under F-017; it is not silently suppressed.

## 4. Cross-engine and release evidence

- Real SAS ODA production: 34/34 stages PASS.
- SAS/R ADTTE exact reconciliation: PASS; production and validation each contain 2,058 records.
- Admiral ADSL/OS/PFS scoped reconciliation: PASS, zero cell differences.
- Synthetic comparator bridge: PASS; comparator remains TFL-only and non-confirmatory.
- TFL population contract: PASS (`Rscript tests/test_tfl_population_contract.R`).
- Metadata/spec-to-data, reviewer package, eCTD, and log-cleanliness stages: PASS.

The green DAG demonstrates reproducible execution and cross-language agreement. It does not resolve the S3-04 clinical interpretation decision; correlated tracks can reproduce the same unresolved rule.

## Phase 2 closure addendum — 2026-08-04

The S3-04 disposition is superseded for the controlled Path A implementation by Antony Bevan's adoption of ED-01–ED-07. Separate SAS and R tracks now consume staged SV/PN/CM/PR, apply the adopted pain and CM+PR rules, retain diary/RT/date-bound source lineages, and reconcile against TTUMOR ITT-primary ADTTE. The historical baseline remains in this audit for auditability. Final full-DAG/reseal and CI verification are complete; external qualified statistical/medical review remains required before any regulated or filing-facing use.

## 5. Handoff to Section 4

Section 4 should verify Define/ARM/TFL metadata against the corrected ADTTE fields and counts, ensure package copies are byte-aligned with the factory, and carry S3-04 into the reviewer guide and known-differences board. The release posture remains **Path A controlled demonstration**, not a sponsor-approved submission package.
