# F-042 Endpoint Approver Review Packet

**Packet ID:** `F042-APPROVER-PACKET-2026-08-03`<br>
**Version:** `1.0.0`<br>
**Status:** **READY FOR CONTROLLED REVIEW — NO APPROVAL RECORDED**<br>
**Decision record:** [`EDR-F042-T11-8-2026-08-03`](ENDPOINT_DECISION_RECORD_F042_T11_8_2026-08-03.md)<br>
**Approval specification:** [`F042-ENDPOINT-APPROVAL-SPEC-2026-08-03`](F042_ENDPOINT_APPROVAL_SPEC_2026-08-03.md)<br>
**Product boundary:** Path A controlled non-submission demonstration

## 1. Requested action

Review `ED-01` through `ED-07` and record one of the following in the controlled [decision record](ENDPOINT_DECISION_RECORD_F042_T11_8_2026-08-03.md):

- approve all decisions as written;
- approve with exact written modifications, identifying every affected decision; or
- reject/return identified decisions with a written rationale.

This packet is a navigation and review aid. It does not replace the approval specification, record an approval, authorize programming, or constitute a Part 11 electronic signature.

## 2. Why approval is required

The current sealed Path A outputs reproduce the implemented code, but the pain derivation is not clinically conforming and the TTUMOR population and SAP TFL mappings require correction. Reproducibility therefore does not establish endpoint correctness.

Until named approvals are recorded:

- do not modify the sealed ADTTE, TFL, metadata, or package outputs;
- do not describe TTPAIN/PFS as corrected, sponsor-approved, SAP-complete, or filing-ready; and
- keep F-042 open as a disclosed Path A residual.

## 3. Decision summary

| ID | Approval requested | Principal reviewer | Consequence after approval |
|---|---|---|---|
| `ED-01` | Use the specified cancer-related clinical/radiological evidence rule for diary pain progression; do not use PSA alone or later backdating. | Statistician + medical | Reclassifies TTPAIN/PFS pain events. |
| `ED-02` | Stage full PR and use a provenance-preserving CM+PR union for direct-intent palliative/antalgic radiotherapy. | Statistician + medical | Adds omitted RT evidence and prevents PR-only loss. |
| `ED-03` | Produce primary diary-or-RT, diary-only, RT-only, and missing-date analyses. | Statistician | Exposes sensitivity to RT source and date assumptions. |
| `ED-04` | Restore SAP-native `T-11-3`–`T-11-8` identifiers. | Statistician/SAP authority | Changes catalog, output labels, metadata, and reviewer traceability. |
| `ED-05` | Use ITT for primary TTUMOR; retain measurable disease as supportive only. | Statistician/SAP authority | Changes the TTUMOR denominator and dependent results. |
| `ED-06` | Use `RANDDT` for efficacy TTE parameters and `TRTSDT` for TTSAE. | Statistician/SAP authority | Locks time origins and removes reviewer-guide conflict. |
| `ED-07` | Replace the current pain algorithm with the component-specific signed rule. | Statistician + medical | Changes visit summaries, triggers, confirmation, event dates, and censoring. |

## 4. Focused clinical and statistical confirmations

These are the highest-judgment provisions inside `ED-01`, `ED-02`, and `ED-07`. The statistician and medical reviewer should explicitly verify them before signing the parent record.

| Confirmation | Proposed rule requiring explicit review | Statistician initials | Medical initials |
|---|---|---|---|
| Reference value | Use baseline/reference PPI rather than nadir for the corrected analysis. | — | — |
| Baseline AS of zero | The percentage-change analgesic branch is non-evaluable when baseline mean AS is zero unless a signed amendment supplies an absolute-change rule. | — | — |
| Confirmation sequence | Require the same component at the immediately next scheduled pain evaluation, at least 21 days later; do not bridge an intervening missing/non-evaluable scheduled assessment. | — | — |
| Event dating | Date a confirmed diary event at the first qualifying visit using complete `SVSTDTC`, with maximum complete diary date as a flagged fallback. | — | — |
| Cancer-related support | Accept qualifying radiological/clinical progression no later than the confirming visit; PSA alone does not certify pain progression. | — | — |
| Week-only clinical dates | For `DSSTWK`, reconstruct the point date from randomization and require `point date + 4 days <= confirming visit date` in the primary analysis. | — | — |
| Palliative RT | Automatically qualify only direct-intent local radiation text containing `PALLIATIVE` or `ANTALGIC`; exclude generic/prior radiation and radiopharmaceuticals. | — | — |
| Missing/partial RT date | Exclude from the primary exact-date event derivation and retain for bounded sensitivity/adjudication. | — | — |

Initials in this table document review but do not replace the named signatures and approval election in the decision record.

## 5. Evidence reviewers should understand

| Evidence | Observed result | Interpretation |
|---|---:|---|
| Current pain-labelled PFS records | 37 | Historical inventory from the non-conforming algorithm; not an approval denominator. |
| PN subject-visits / exact SV matches | 1,937 / 1,931 | Supports the proposed SV-first event-date hierarchy; six visits require fallback or source review. |
| Direct-intent CM RT | 13 rows / 10 subjects | Twelve complete start dates, all post-randomization. |
| Direct-intent PR RT | 3 rows / 1 subject | Complete post-randomization dates. |
| Direct-intent CM/PR subject overlap | 0 | PR cannot be the sole RT source. |
| Observed Cycle 1 seven-day baseline mean AS equal to zero | 110 of 324 subjects with an observed window; 106 meet 5-of-7 | A 25% increase is mathematically undefined at zero; the proposed primary branch treats it as non-evaluable. |
| Current TTUMOR implementation | ITT ∩ measurable disease | Proposed primary population is ITT; measurable disease remains supportive. |

The [impact appendix](F042_PFS_PAIN_IMPACT_APPENDIX_2026-08-03.md) explains why corrected event counts and treatment effects cannot be inferred from the current 37 labels without full re-derivation.

## 6. Evidence manifest

Review in this order:

1. [Endpoint approval specification](F042_ENDPOINT_APPROVAL_SPEC_2026-08-03.md) — exact proposed rules and post-signature acceptance criteria.
2. [Endpoint decision record](ENDPOINT_DECISION_RECORD_F042_T11_8_2026-08-03.md) — approval election, per-decision disposition, and signature fields.
3. [PFS/pain impact appendix](F042_PFS_PAIN_IMPACT_APPENDIX_2026-08-03.md) — current-output impact and limitations.
4. [CM/PR source qualification audit](F042_PR_SOURCE_QUALIFICATION_AUDIT_2026-08-03.md) — source availability, classification, and precedence evidence.
5. [Section 2 endpoint audit](../../../06_qc_evidence/audit/section_reviews/SECTION_02_POPULATIONS_ENDPOINTS_AUDIT_2026-08-03.md) and [Section 3 ADaM audit](../../../06_qc_evidence/audit/section_reviews/SECTION_03_ADAM_DERIVATION_AUDIT_2026-08-03.md) — historical implementation findings.

## 7. Approval completeness check

Approval is complete only when:

- every `ED-01`–`ED-07` row has exactly one disposition;
- all modifications contain exact replacement wording;
- the sponsor statistician and medical reviewer have completed their applicable review;
- programming has confirmed source availability and implementation feasibility;
- independent QC has confirmed that the specification is testable;
- all required names, signatures, and dates are present in the decision record; and
- the signed artifact or governed approval evidence is linked without claiming that Git itself is an electronic signature.

After complete approval, Phase 2 may implement the signed rules independently in SAS and R. The resulting endpoint package remains unapproved until subject-level reconciliation, full DAG execution, output/metadata regeneration, independent QC, and reseal all pass.
