# Endpoint Decision Record — F-042 / T-11-8

**Record ID:** `EDR-F042-T11-8-2026-08-03`<br>
**Version:** `0.3.2`<br>
**Status:** **AUTHOR-DECISION READY — PENDING ACCOUNTABLE-AUTHOR SIGN-OFF**<br>
**Product path:** Path A — controlled non-submission demonstration<br>
**Baseline commit:** `a213667` (`codex/submission-pipeline-rc`)<br>
**Change class:** Analysis-specification and output-catalog decision; no derivation change in this record

## 1. Purpose and control boundary

This record turns the open endpoint issues into explicit decisions that can be adopted, revised, rejected, or superseded. It is a decision-control artifact, not sponsor or medical approval. The exact recommended implementation is defined in the [`F-042 Endpoint Approval Specification`](F042_ENDPOINT_APPROVAL_SPEC_2026-08-03.md), which remains non-executable until the accountable author signs this record.

The current validated ADTTE, TFL, metadata, and release outputs remain unchanged. Until the required decisions are author-adopted, no program may silently promote the current pain component to an SAP-complete PFS rule or treat the current response block as the SAP `T-11-8` TTPAIN deliverable.

The separate [provisional implementation note](F042_PROVISIONAL_IMPLEMENTATION_NOTE_2026-08-03.md)
records a bounded author-directed exploratory program. That artifact may inspect
the proposed rules and quantify provisional impact, but it cannot consume the
decision as production authority, modify/reseal Path A outputs, or represent
formal author adoption before the signed record is complete.

The associated [CM/PR adjudication worksheet specification](F042_ADJUDICATION_WORKSHEET_SPEC_2026-08-03.md)
defines the local, patient-level review fields and disposition controls. It does
not place patient-level records in Git and does not replace the signed decision.

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
- A direct-intent CM review found 13 palliative/antalgic radiotherapy rows across 10 subjects, including 12 complete post-randomization start dates. Direct-intent PR contains 3 rows for 1 different subject. PR therefore cannot be the sole endpoint source.
- The current pain implementation does not match the protocol/corrected-publication rule: it uses median AS, `PPI >=2`, absolute `AS >=10`, combined-component confirmation, and a terminal-trigger exception. These rules must be replaced after accountable-author adoption and before the endpoint can be represented as corrected for Path A.
- PN-to-SV profiling found exact SV visit-date matches for 1,931 of 1,937 PN subject-visits, supporting a controlled `SVSTDTC` event-date hierarchy with a flagged fallback.

The numerical agreement above proves reproducibility of the current rule. It does not approve the unresolved clinical interpretation.

## 3. Decision register

| ID | Decision question | Current state | Proposed controlled direction | Decision gate | Downstream impact |
|---|---|---|---|---|---|
| `ED-01` | What disease evidence qualifies pain progression for TTPAIN and PFS? | The protocol requires cancer-related clinical and/or radiological support; the current implementation has no adopted operational rule. | **Recommended:** apply Approval Specification §§3–5. Accept qualifying radiological/clinical progression no later than the confirming visit, or direct-intent palliative/antalgic RT. Do not use PSA alone to certify pain and do not backdate from later evidence. | Accountable author for Path A; external statistical/medical review before regulated reuse | TTPAIN/PFS `EVNTDESC`, `ADT`, `CNSR`, `AVAL`, event counts, medians, HRs, and sensitivity outputs. |
| `ED-02` | Which sources and precedence govern palliative radiotherapy? | PR has 11 broad radiation-screen rows, but direct-intent evidence is split across non-overlapping CM and PR subjects. | **Recommended:** stage full PR and use the controlled CM+PR union in Approval Specification §6. Direct-intent text requires both a radiation concept and `PALLIATIVE`/`ANTALGIC`; generic or prior radiation is not auto-qualified. | Accountable author for Path A; external statistical/medical review before regulated reuse | SDTM staging, ADTTE PFS/TTPAIN, source traceability, and reviewer guides. |
| `ED-03` | What palliative-RT sensitivity set is required? | RT is a protocol pain-progression criterion; no controlled source-isolation analysis exists. | **Recommended:** primary diary-or-RT analysis plus diary-only sensitivity, RT-only supportive analysis and bounded missing-date review per Approval Specification §7. | Accountable author for Path A; external statistical review before regulated reuse | PFS/TTPAIN event composition, summaries and lineage. |
| `ED-04` | How is the SAP `T-11-8` collision resolved? | SAP Table 22 assigns `T-11-3` PSA response, `T-11-4` ORR, `T-11-5` pain response and `T-11-8` TTPAIN; the current catalog/physical block is wrong. | **Recommended:** restore the complete SAP-native `T-11-3`–`T-11-8` mapping in Approval Specification §8. Do not invent an extension for the primary PSA/ORR results. | Accountable author for Path A; sponsor/SAP authority before regulated reuse | TFL catalog, ARM/ARS, Define, traceability matrix, package, and reviewer narrative. |
| `ED-05` | What population governs TTUMOR? | Current Path A ADTTE incorrectly uses ITT ∩ measurable disease (`MEASDISF='Y'`). Protocol/publication evidence and SAP Table 22 support ITT. | **Recommended:** one TTUMOR record per ITT subject; retain measurable disease as supportive subgroup/sensitivity only. ORR remains measurable-disease restricted. | Accountable author for Path A; sponsor/SAP authority before regulated reuse | TTUMOR dens, shells, estimand wording, and metadata. |
| `ED-06` | What are the time origins for secondary TTE parameters? | Code uses `RANDDT` for OS/PFS/TTPAIN/TTPSA/TTUMOR and `TRTSDT` for TTSAE; one reviewer-guide passage conflicts. | **Recommended:** adopt the current parameter-level origins in Approval Specification §9 and correct reviewer-facing text. | Accountable author for Path A; sponsor/SAP authority before regulated reuse | `STARTDT`, `AVAL`, ADRG, traceability, and Define methods. |
| `ED-07` | What exact pain progression algorithm is authorized? | Current code uses the wrong PPI/AS thresholds and AS summary, can confirm across different components, and accepts a terminal single trigger. | **Recommended:** component-specific 5-of-7 summaries; PPI median increase `>=1`; mean AS increase `>=25%` with positive baseline; same component at two consecutive scheduled evaluations at least 21 days apart; do not bridge an intervening missing/non-evaluable visit; no terminal exception; RT standalone; SV visit-date hierarchy. | Accountable author for Path A; external statistical/medical review before regulated reuse | TTPAIN and PFS derivations, event dating, censoring, source traceability and regression scope. |

## 4. Required accountable-author decision

No decision is recorded by this unsigned document. Use the [`F-042 Endpoint Approver Review Packet`](F042_APPROVER_REVIEW_PACKET_2026-08-03.md) to conduct the review, then record the accountable Path A disposition below.

### Author decision election

- [ ] **ADOPT AS WRITTEN FOR PATH A** — adopt `ED-01` through `ED-07` and authorize implementation of Approval Specification §§3–10.
- [ ] **ADOPT WITH DOCUMENTED MODIFICATIONS FOR PATH A** — attach exact replacement wording and identify affected decision IDs.
- [ ] **REJECT / RETURN FOR REVISION** — identify rejected decision IDs and rationale.

If decisions are dispositioned individually, complete every row:

| Decision | Adopt as written | Modify (attach wording) | Reject | Accountable-author initials |
|---|---|---|---|---|
| `ED-01` | [ ] | [ ] | [ ] | — |
| `ED-02` | [ ] | [ ] | [ ] | — |
| `ED-03` | [ ] | [ ] | [ ] | — |
| `ED-04` | [ ] | [ ] | [ ] | — |
| `ED-05` | [ ] | [ ] | [ ] | — |
| `ED-06` | [ ] | [ ] | [ ] | — |
| `ED-07` | [ ] | [ ] | [ ] | — |

| Role | Required action | Name / signature | Date | Status |
|---|---|---|---|---|
| Accountable author / project owner | Adopt, modify, or reject ED-01–ED-07; acknowledge the single-author limitations below | — | — | **Pending** |
| External statistician/medical reviewer | Required before regulated, sponsor, or filing use; optional enhancement for Path A | Not available | — | **Not performed** |

### Single-author limitation acknowledgement

By signing, the accountable author acknowledges that:

- the same person performed the evidence review, selected the proposed interpretation, and will direct implementation;
- no independent human statistician, medical reviewer, programming lead, or QC unit is represented;
- adoption authorizes only the Path A controlled non-submission demonstration;
- separate SAS/R implementations, automated tests, subject-level reconciliation, and a documented delayed second-pass review mitigate—but do not eliminate—the lack of independent human review; and
- external qualified statistical and medical review, sponsor governance, and applicable validated-system controls remain required before regulated or filing use.

The accountable-author signature is a project decision record, not sponsor approval, independent medical/statistical approval, or a Part 11 electronic signature. Blank fields must not be replaced with invented identity or approval metadata.

By signing, the author confirms that any modification is written into the controlled record or an identified attachment. Verbal qualifications and unlinked statements are not executable authority.

## 5. Implementation gate for the next phase

Phase 2 programming is **blocked** until the accountable author has signed and dated an explicit disposition for ED-01 through ED-07 and acknowledged the single-author limitations. A partially dispositioned record is non-executable unless the signed text explicitly authorizes a bounded subset that has no dependency on unresolved decisions.

After accountable-author adoption, the implementation order is:

1. Stage full PR and construct the author-adopted CM+PR candidate union with provenance.
2. Implement the author-adopted visit-level pain summaries, confirmation rule, event-date hierarchy and cancer-related qualification separately in SAS and R.
3. Implement the author-adopted primary, diary-only, RT-only and missing-date analyses.
4. Expand TTUMOR to ITT and retain the measurable-disease supportive analysis.
5. Restore the SAP-native `T-11-3`–`T-11-8` catalog and physical mappings; update metadata/reviewer documents.
6. Reconcile separately programmed SAS/R results and scoped admiral checks; quantify every event and denominator reclassification.
7. Rerun the complete DAG and reseal only after all output and traceability checks pass.

If author adoption is not recorded, retain the current Path A labels and the explicit F-042 residual. Do not change the validated analysis merely to make the catalog appear complete.

## 6. Companion evidence

- [Approver review packet](F042_APPROVER_REVIEW_PACKET_2026-08-03.md)
- [F-042 impact appendix](F042_PFS_PAIN_IMPACT_APPENDIX_2026-08-03.md)
- [Author-decision-ready endpoint specification](F042_ENDPOINT_APPROVAL_SPEC_2026-08-03.md)
- [Machine-readable decision state](endpoint_decision_record_F042_T11_8_2026-08-03.yaml)
- [PR source qualification audit](F042_PR_SOURCE_QUALIFICATION_AUDIT_2026-08-03.md)
- [Machine-readable PR source profile](F042_PR_SOURCE_QUALIFICATION_AUDIT_2026-08-03.yaml)
- [Section 2 population/endpoint audit](../../../06_qc_evidence/audit/section_reviews/SECTION_02_POPULATIONS_ENDPOINTS_AUDIT_2026-08-03.md)
- [Section 3 ADaM audit](../../../06_qc_evidence/audit/section_reviews/SECTION_03_ADAM_DERIVATION_AUDIT_2026-08-03.md)
- [Section 4 metadata/TFL audit](../../../06_qc_evidence/audit/section_reviews/SECTION_04_METADATA_TFL_REVIEWER_PACKAGE_AUDIT_2026-08-03.md)
