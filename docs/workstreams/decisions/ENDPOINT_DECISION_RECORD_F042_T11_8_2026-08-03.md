# Endpoint Decision Record — F-042 / T-11-8

**Record ID:** `EDR-F042-T11-8-2026-08-03`<br>
**Version:** `0.1.0`<br>
**Status:** **DRAFT — PENDING SPONSOR/STATISTICIAN/MEDICAL APPROVAL**<br>
**Product path:** Path A — controlled non-submission demonstration<br>
**Baseline commit:** `a213667` (`codex/submission-pipeline-rc`)<br>
**Change class:** Analysis-specification and output-catalog decision; no derivation change in this record

## 1. Purpose and control boundary

This record turns the open endpoint issues into explicit decisions that can be approved, rejected, or superseded. It is a decision-control artifact, not an approval and not an executable specification.

The current validated ADTTE, TFL, metadata, and release outputs remain unchanged. Until the required decisions are approved, no program may silently promote the current pain component to an SAP-complete PFS rule or treat the current response block as the SAP `T-11-8` TTPAIN deliverable.

This record is subordinate to:

1. [`docs/PRODUCT_CLAIM.md`](../../PRODUCT_CLAIM.md) — allowed product claims and Path A boundary.
2. SAP v4.0 and [`06_qc_evidence/audit/SAP_LOCK_REVIEW_MEMO.md`](../../../06_qc_evidence/audit/SAP_LOCK_REVIEW_MEMO.md) — programming authority, not sponsor filing approval.
3. [`06_qc_evidence/audit/FINDINGS_DISPOSITION_BOARD.md`](../../../06_qc_evidence/audit/FINDINGS_DISPOSITION_BOARD.md) — F-042 disposition.
4. The Section 2 and Section 3 audits — observed implementation and impact evidence.

## 2. Evidence baseline

The baseline is the final real-SAS run used by the current Path A release evidence:

- Real SAS ODA, full 34-stage DAG, `pipeline_health=GREEN`.
- SAS/R ADTTE output contract: 2,058 records with exact row/parameter shape.
- Scoped admiral ADSL/OS/PFS reconciliation: zero cell differences.
- Release verification at the baseline: 30/30 checks passed.
- Current PFS component labels: 282 disease-progression events, 37 pain-progression candidate events, 8 death events, and 44 censored records in the real MP ADTTE.
- Raw SDTM PR exists, but PR is not in the current staging handoff or ADaM derivation.
- Pre-implementation PR source profile is complete: 151 rows, 65 subjects, 0 duplicate `USUBJID/PRSEQ` keys, 148 complete ISO dates, and 65/65 ADSL linkages; endpoint consumption remains blocked.

The numerical agreement above proves reproducibility of the current rule. It does not approve the unresolved clinical interpretation.

## 3. Decision register

| ID | Decision question | Current state | Proposed controlled direction | Approval gate | Downstream impact |
|---|---|---|---|---|---|
| `ED-01` | What disease evidence qualifies pain progression as a PFS event? | The SAP requires supporting disease evidence; the current implementation labels pain-led candidates but has no approved qualification hierarchy or time window. | Approve an explicit evidence set, hierarchy, and time window. Candidate sources for adjudication may include RECIST, PSA, bone/other disease assessments, or another sponsor-authorized source; this list is not yet a rule. | Sponsor statistician + medical reviewer | PFS `EVNTDESC`, `ADT`, `CNSR`, `AVAL`, event counts, medians, HRs, and sensitivity outputs. |
| `ED-02` | Which source and precedence govern palliative radiotherapy? | Eleven radiation-related PR rows across nine subjects are present in raw source; PR is not staged. CM contains historical/prior radiation records and cannot safely be treated as equivalent without a rule. | Recommended for approval: stage PR as the primary procedure source and define whether CM is corroborative, historical, or excluded; specify date precedence and treatment intent handling. | Sponsor statistician + medical reviewer | SDTM staging, ADTTE PFS/TTPAIN, source traceability, and reviewer guides. |
| `ED-03` | What palliative-RT-only sensitivity is required? | SAP §10.4 mentions palliative radiotherapy; no controlled sensitivity output exists. | Pre-specify a palliative-RT-only sensitivity before programming. At minimum, compare the approved supporting-disease rule with an explicit RT-only exclusion/qualification scenario; record any different sponsor-required scenario before coding. | Sponsor statistician | PFS event composition and all PFS summaries; possible TTPAIN sensitivity. |
| `ED-04` | How is the SAP `T-11-8` collision resolved? | SAP Appendix D/Table 22 calls `T-11-8` TTPAIN; the physical block is PSA response + ORR. | Recommended: restore TTPAIN to `T-11-8` and move the response summary to an approved extension identifier. The exact extension ID must be approved; do not invent one in code. | SAP/statistician authority | TFL catalog, ARM/ARS, Define, traceability matrix, package, and reviewer narrative. |
| `ED-05` | What population governs TTUMOR? | Current Path A ADTTE uses ITT ∩ measurable disease (`MEASDISF='Y'`), while SAP Table 22 wording is broader. | Retain the endpoint-specific measurable implementation for Path A and obtain an explicit SAP clarification before any filing-facing claim. | Statistician/SAP authority | TTUMOR dens, shells, estimand wording, and metadata. |
| `ED-06` | What are the time origins for secondary TTE parameters? | Code uses `RANDDT` for OS/PFS/TTPAIN/TTPSA/TTUMOR and `TRTSDT` for TTSAE; one reviewer-guide passage conflicts. | Approve the current parameter-level origins and correct all reviewer-facing text. This is a documentation synchronization, not a new derivation rule. | Statistician/SAP authority | `STARTDT`, `AVAL`, ADRG, traceability, and Define methods. |

## 4. Required approval record

No approval is recorded by this document.

| Role | Required action | Name / signature | Date | Status |
|---|---|---|---|---|
| Sponsor statistician | Approve or reject ED-01, ED-03, ED-04, ED-05, ED-06 | — | — | **Pending** |
| Medical reviewer | Approve disease-evidence and palliative-RT interpretation in ED-01–ED-03 | — | — | **Pending** |
| Programming lead | Confirm implementation impact and regression scope after approval | — | — | **Pending** |
| QC/independent reviewer | Confirm rerun and traceability evidence after implementation | — | — | **Pending** |

An email, meeting minute, or signed amendment may be attached or linked only after it is available. Blank fields must not be replaced with invented approval metadata.

## 5. Implementation gate for the next phase

Phase 2 programming is **blocked** until ED-01 through ED-04 have an explicit approved disposition. ED-05 and ED-06 must be recorded as approved clarification or documented Path A scope-out before metadata/output reseal.

After approval, the implementation order is:

1. Stage and profile PR; define source precedence and provenance fields.
2. Implement the approved pain-supporting-disease rule in SAS and R.
3. Add the approved palliative-RT sensitivity analysis.
4. Reconcile SAS/R and scoped admiral results; quantify every event reclassification.
5. Resolve the T-11-8 catalog mapping and update metadata/reviewer documents.
6. Rerun the complete DAG and reseal only after all output and traceability checks pass.

If approval is not obtained, retain the current Path A labels and the explicit F-042 residual. Do not change the validated analysis merely to make the catalog appear complete.

## 6. Companion evidence

- [F-042 impact appendix](F042_PFS_PAIN_IMPACT_APPENDIX_2026-08-03.md)
- [Machine-readable decision state](endpoint_decision_record_F042_T11_8_2026-08-03.yaml)
- [PR source qualification audit](F042_PR_SOURCE_QUALIFICATION_AUDIT_2026-08-03.md)
- [Machine-readable PR source profile](F042_PR_SOURCE_QUALIFICATION_AUDIT_2026-08-03.yaml)
- [Section 2 population/endpoint audit](../../../06_qc_evidence/audit/section_reviews/SECTION_02_POPULATIONS_ENDPOINTS_AUDIT_2026-08-03.md)
- [Section 3 ADaM audit](../../../06_qc_evidence/audit/section_reviews/SECTION_03_ADAM_DERIVATION_AUDIT_2026-08-03.md)
- [Section 4 metadata/TFL audit](../../../06_qc_evidence/audit/section_reviews/SECTION_04_METADATA_TFL_REVIEWER_PACKAGE_AUDIT_2026-08-03.md)
