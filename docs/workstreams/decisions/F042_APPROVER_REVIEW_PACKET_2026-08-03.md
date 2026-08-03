# F-042 Endpoint Approver Review Packet

**Packet ID:** `F042-APPROVER-PACKET-2026-08-03`<br>
**Version:** `1.1.0`<br>
**Status:** **READY FOR ACCOUNTABLE-AUTHOR REVIEW — NO DECISION RECORDED**<br>
**Decision record:** [`EDR-F042-T11-8-2026-08-03`](ENDPOINT_DECISION_RECORD_F042_T11_8_2026-08-03.md)<br>
**Approval specification:** [`F042-ENDPOINT-APPROVAL-SPEC-2026-08-03`](F042_ENDPOINT_APPROVAL_SPEC_2026-08-03.md)<br>
**Product boundary:** Path A controlled non-submission demonstration

## 1. Requested action

As accountable author and project owner, review `ED-01` through `ED-07` and record one of the following in the controlled [decision record](ENDPOINT_DECISION_RECORD_F042_T11_8_2026-08-03.md):

- adopt all decisions as written for Path A;
- adopt with exact written modifications, identifying every affected decision; or
- reject/return identified decisions with a written rationale.

This packet is a navigation and review aid. It does not replace the specification, record a decision, authorize programming by itself, or constitute sponsor approval, independent review, or a Part 11 electronic signature.

## 2. Single-author governance boundary

This is a one-person project. The same person is the project owner, analyst, programmer, and QC reviewer. The Path A control model therefore uses one accountable-author decision instead of fictitious sponsor-team signatures.

The author decision can authorize work only for the controlled non-submission demonstration. It cannot represent:

- independent statistical or medical review;
- sponsor, institutional, or regulatory authorization;
- organizational segregation of duties;
- validated-system or Part 11 compliance; or
- fitness for filing or clinical decision-making.

The lack of independent human review is mitigated through separately programmed SAS/R derivations, automated regression tests, subject-level reconciliation, immutable Git history, and a documented delayed second-pass review. These controls reduce error risk but do not make the review independent.

## 3. Why an author decision is required

The current sealed Path A outputs reproduce the implemented code, but the pain derivation is not clinically conforming and the TTUMOR population and SAP TFL mappings require correction. Reproducibility therefore does not establish endpoint correctness.

Until the accountable-author decision is signed and dated:

- do not modify the sealed ADTTE, TFL, metadata, or package outputs;
- do not describe TTPAIN/PFS as corrected, sponsor-approved, SAP-complete, or filing-ready; and
- keep F-042 open as a disclosed Path A residual.

## 4. Decision summary

| ID | Path A decision requested | Decision owner | Consequence after adoption |
|---|---|---|---|
| `ED-01` | Use the specified cancer-related clinical/radiological evidence rule for diary pain progression; do not use PSA alone or later backdating. | Accountable author | Reclassifies TTPAIN/PFS pain events. |
| `ED-02` | Stage full PR and use a provenance-preserving CM+PR union for direct-intent palliative/antalgic radiotherapy. | Accountable author | Adds omitted RT evidence and prevents PR-only loss. |
| `ED-03` | Produce primary diary-or-RT, diary-only, RT-only, and missing-date analyses. | Accountable author | Exposes sensitivity to RT source and date assumptions. |
| `ED-04` | Restore SAP-native `T-11-3`–`T-11-8` identifiers. | Accountable author | Changes catalog, output labels, metadata, and reviewer traceability. |
| `ED-05` | Use ITT for primary TTUMOR; retain measurable disease as supportive only. | Accountable author | Changes the TTUMOR denominator and dependent results. |
| `ED-06` | Use `RANDDT` for efficacy TTE parameters and `TRTSDT` for TTSAE. | Accountable author | Locks time origins and removes reviewer-guide conflict. |
| `ED-07` | Replace the current pain algorithm with the component-specific adopted rule. | Accountable author | Changes visit summaries, triggers, confirmation, event dates, and censoring. |

## 5. Focused clinical and statistical confirmations

These are the highest-judgment provisions inside `ED-01`, `ED-02`, and `ED-07`. The accountable author must explicitly review them before signing the parent record. The external-review column remains available for any future qualified reviewer and is required before regulated reuse.

| Confirmation | Proposed rule requiring explicit review | Accountable-author initials | Future external review |
|---|---|---|---|
| Reference value | Use baseline/reference PPI rather than nadir for the corrected analysis. | — | Not performed |
| Baseline AS of zero | The percentage-change analgesic branch is non-evaluable when baseline mean AS is zero unless a controlled amendment supplies an absolute-change rule. | — | Not performed |
| Confirmation sequence | Require the same component at the immediately next scheduled pain evaluation, at least 21 days later; do not bridge an intervening missing/non-evaluable scheduled assessment. | — | Not performed |
| Event dating | Date a confirmed diary event at the first qualifying visit using complete `SVSTDTC`, with maximum complete diary date as a flagged fallback. | — | Not performed |
| Cancer-related support | Accept qualifying radiological/clinical progression no later than the confirming visit; PSA alone does not certify pain progression. | — | Not performed |
| Week-only clinical dates | For `DSSTWK`, reconstruct the point date from randomization and require `point date + 4 days <= confirming visit date` in the primary analysis. | — | Not performed |
| Palliative RT | Automatically qualify only direct-intent local radiation text containing `PALLIATIVE` or `ANTALGIC`; exclude generic/prior radiation and radiopharmaceuticals. | — | Not performed |
| Missing/partial RT date | Exclude from the primary exact-date event derivation and retain for bounded sensitivity/adjudication. | — | Not performed |

Initials in this table document review but do not replace the accountable-author signature and decision election in the decision record.

## 6. Evidence the author should understand

| Evidence | Observed result | Interpretation |
|---|---:|---|
| Current pain-labelled PFS records | 37 | Historical inventory from the non-conforming algorithm; not an author-adoption denominator. |
| PN subject-visits / exact SV matches | 1,937 / 1,931 | Supports the proposed SV-first event-date hierarchy; six visits require fallback or source review. |
| Direct-intent CM RT | 13 rows / 10 subjects | Twelve complete start dates, all post-randomization. |
| Direct-intent PR RT | 3 rows / 1 subject | Complete post-randomization dates. |
| Direct-intent CM/PR subject overlap | 0 | PR cannot be the sole RT source. |
| Observed Cycle 1 seven-day baseline mean AS equal to zero | 110 of 324 subjects with an observed window; 106 meet 5-of-7 | A 25% increase is mathematically undefined at zero; the proposed primary branch treats it as non-evaluable. |
| Current TTUMOR implementation | ITT ∩ measurable disease | Proposed primary population is ITT; measurable disease remains supportive. |

The [impact appendix](F042_PFS_PAIN_IMPACT_APPENDIX_2026-08-03.md) explains why corrected event counts and treatment effects cannot be inferred from the current 37 labels without full re-derivation.

## 7. Evidence manifest

Review in this order:

1. [Endpoint approval specification](F042_ENDPOINT_APPROVAL_SPEC_2026-08-03.md) — exact proposed rules and post-adoption acceptance criteria.
2. [Endpoint decision record](ENDPOINT_DECISION_RECORD_F042_T11_8_2026-08-03.md) — author election, per-decision disposition, limitation acknowledgement, and signature field.
3. [PFS/pain impact appendix](F042_PFS_PAIN_IMPACT_APPENDIX_2026-08-03.md) — current-output impact and limitations.
4. [CM/PR source qualification audit](F042_PR_SOURCE_QUALIFICATION_AUDIT_2026-08-03.md) — source availability, classification, and precedence evidence.
5. [Section 2 endpoint audit](../../../06_qc_evidence/audit/section_reviews/SECTION_02_POPULATIONS_ENDPOINTS_AUDIT_2026-08-03.md) and [Section 3 ADaM audit](../../../06_qc_evidence/audit/section_reviews/SECTION_03_ADAM_DERIVATION_AUDIT_2026-08-03.md) — historical implementation findings.

## 8. Author-decision completeness check

Path A authorization is complete only when:

- every `ED-01`–`ED-07` row has exactly one disposition;
- all modifications contain exact replacement wording;
- the accountable author has reviewed every focused confirmation;
- the single-author limitation acknowledgement is accepted;
- the accountable-author name, signature, and date are present in the decision record; and
- the signed artifact or controlled decision evidence is linked without claiming that Git itself is an electronic signature.

After the complete author decision, Phase 2 may implement the adopted rules separately in SAS and R. The resulting Path A endpoint package remains non-independent and non-regulated even after subject-level reconciliation, delayed second-pass author review, full DAG execution, output/metadata regeneration, automated QC, and reseal. Qualified external statistical/medical review and sponsor governance remain mandatory before any regulated reuse.
