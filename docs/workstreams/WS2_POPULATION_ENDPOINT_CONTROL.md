# WS-2 Population & Endpoint Control Table

**Workstream:** Statistical Specification (G02)  
**Product claim:** Path A  
**As of:** 2026-08-03
**Authorities:** SAP v4.0 · `config/study_config.yaml` · `config/tfl_output_catalog.yaml` · ADRG · [Section 2 audit](../../06_qc_evidence/audit/section_reviews/SECTION_02_POPULATIONS_ENDPOINTS_AUDIT_2026-08-03.md)

**Decision handoff:** Begin with the [F-042 accountable-author review packet](decisions/F042_APPROVER_REVIEW_PACKET_2026-08-03.md), then record the author decision in the [F-042 / T-11-8 Endpoint Decision Record](decisions/ENDPOINT_DECISION_RECORD_F042_T11_8_2026-08-03.md). The controlled evidence includes the [approval specification](decisions/F042_ENDPOINT_APPROVAL_SPEC_2026-08-03.md), [quantified impact appendix](decisions/F042_PFS_PAIN_IMPACT_APPENDIX_2026-08-03.md), and [CM/PR source qualification audit](decisions/F042_PR_SOURCE_QUALIFICATION_AUDIT_2026-08-03.md). The package is author-decision ready/pending accountable-author sign-off and does not change current Path A outputs. It does not claim independent, sponsor, or regulated approval.

---

## 1. Purpose

Make G02 concrete: every **population** and **endpoint** used in controlled outputs maps to:

- SAP / config source  
- ADaM location  
- Controlled TFL (or deferred)  
- Residual / disclosure  

If it is not in this table, programming should not invent it for Path A.

---

## 2. Populations

| Population | Flag / rule | ADaM | Used in controlled outputs | Notes / residual |
|---|---|---|---|---|
| **ITT** | `ITTFL='Y'` | ADSL → carried to ADTTE | OS, PFS, TTPSA; author-decision proposal also requires TTUMOR and TTPAIN | MP N=371; synthetic CbzP N=378; combined N=749 is not protocol ITT N=755. |
| **Safety** | `SAFFL='Y'` | ADSL | ADAE TEAE tables T-20; lab shifts T-21; exposure | MP N=371; synthetic CbzP N=371. Denominators use SAFFL, not AE-distinct N. |
| **Measurable disease** | `MEASDISF='Y'` | ADSL | ORR response summary; current TTUMOR implementation only | Current ORR dens = **all** MEAS subjects left-join ADRS OBJRESP: MP N=203, CbzP N=179. Signed proposal moves primary TTUMOR to ITT and retains MEAS only as support. |
| **Package combined display** | Real MP + synthetic CbzP | TFL merge only | Comparative figures/tables | **Not** protocol ITT 755 (F-012) |
| **PSA response analysis set** | `PSARESP` rows joined to ADSL baseline PSA, excluding controlled fallback (`PSABLIF='Y'`), and filtered `PSABL >= 20` | ADRS + ADSL | PSA response in the current T-11 response block and F-13-1 | **F-011 resolved:** MP 61/329; CbzP 145/361; 690 unique eligible subjects. Synthetic rows without `PSABLIF` are treated as observed. |
| **Pain progression** | Current ADTTE `PARAMCD='TTPAIN'`; author-decision proposal replaces the non-conforming pain algorithm | ADTTE | Not a separate controlled Path A TFL | SAP assigns TTPAIN to T-11-8. Approval Specification ED-07 corrects visit summaries, thresholds, confirmation, RT handling and event dating before implementation. |

### Population hard rules

1. Never label N=749 as original-trial ITT.  
2. Safety tables: safety N from ADSL SAFFL by arm.  
3. MP-only recon ADaM remains the dual-lang truth set.

---

## 3. Endpoints & parameters (controlled)

| Endpoint / param | PARAMCD / measure | Population | Primary ADaM | Controlled TFL IDs | Config / SAP hooks |
|---|---|---|---|---|---|
| Overall survival | OS | ITT | ADTTE | F-11-1, forest F-12-1 | Results recon LIFETEST; randomization origin |
| Progression-free survival | PFS (composite: tumour/PSA/pain/death + NACT censor) | ITT | ADTTE | F-11-2 | SAP v4 PFS hierarchy; randomization origin |
| Time to tumor progression | TTUMOR | Current: ITT ∩ `MEASDISF='Y'`; author-adopted proposal: ITT primary, MEAS supportive | ADTTE | T-11-6 | Protocol/publication and SAP Table 22 support ITT; current denominator must be replaced after author sign-off. |
| Time to PSA progression | TTPSA | ITT | ADTTE | T-11-7 | Physical block and index agree; current CbzP parameter is PH-scaled demonstration data. |
| Time to pain progression | TTPAIN | ITT with author-adopted endpoint evaluability/qualification | ADTTE | SAP target T-11-8; not currently controlled as a TFL | Current five-of-seven/trigger implementation is reproducible but non-conforming; ED-01/02/03/07 define its replacement. |
| PSA response | PSARESP | Observed ADSL baseline PSA >=20 (`PSABLIF != 'Y'`) plus unique PSARESP row | ADRS + ADSL | SAP `T-11-3` after signed remap | F-011 resolved: MP 61/329; CbzP 145/361. |
| Objective response | OBJRESP | MEAS TFL dens; ADRS row = BOR spine | ADRS + TFL left-join | SAP `T-11-4`; response-evaluable `T-11-8b` remains sensitivity | MEAS dens MP 203/CbzP 179; response-evaluable spine MP 351/CbzP 378. |
| TEAE summary | ADAE TRTEMFL etc. | Safety | ADAE | T-20-1, T-20-2 | OCCDS + episode merge |
| Lab CTCAE shift | ADLB grades | Safety | ADLB | T-21-1, T-21-2 | T-21-2 synthetic arm demo |
| Exposure / RDI | ADEX | Safety / treated | ADEX | F-14-1, T-17-*, F-17-1 | Optimus demonstration |
| Disposition / mortality overview | ADSL flags | Display | ADSL | F-01-1 | Not CONSORT flowchart |

### Config parameters that implement clinical rules

From `config/study_config.yaml` (non-exhaustive):

| Parameter | Role |
|---|---|
| `STUDY_CUTOFF_DT` | Administrative censoring |
| `RECIST_*` | Response thresholds / confirm window |
| `PSA_*` | PSA response/progression rules |
| `EPISODE_GAP_DAYS` | ADAE episode merge |
| `BONE_PROG_*` | PCWG3 demonstration in ADRS |
| Lab windows `W_*` | ADLB analysis visits |
| `AGE_STRAT_CUT` | Subgroup forest |

---

## 4. Deferred endpoints / displays (not Path A deliverables)

All IDs in `config/tfl_output_catalog.yaml` → `deferred_not_in_scope` (21 SAP full-catalog IDs), including additional efficacy tables T-11-1…5, T-12-*, T-13-*, T-14-*, T-15/16, F-12-2, T-17-3.

**Programming must not silently implement these without:**

1. Catalog promotion (in-scope + disposition)  
2. Shell / SAP basis  
3. QC plan entry in validation_strategy  

---

## 5. SAP/TFL alignment note

The current Path A TFL text is internally reproducible, but the `T-11-3`–`T-11-8` mappings do not match SAP Appendix D/Table 22. The `T-11-8` TTPAIN/response collision therefore remains explicit and unresolved until the author-adopted rules are implemented and resealed. The proposed Path A disposition restores `T-11-3` PSA response, `T-11-4` ORR, `T-11-5` pain response, `T-11-6` TTUMOR, `T-11-7` TTPSA and `T-11-8` TTPAIN. Primary PSA/ORR results do not require an invented extension ID. No mapping changes occur until accountable-author sign-off.

## 6. Estimand posture (honest)

Path A demonstrates **implementation of endpoint algorithms** suitable for a programming portfolio.  
It does **not** deliver a full ICH E9(R1) estimand package for filing (intercurrent events strategy documentation remains lightweight relative to a sponsor SAP).

CTQ register: `config/ctq_traceability.yaml` + `docs/CTQ_TRACEABILITY_REPORT.md`.

---

## 7. G02 gap acknowledgment

The orchestrator **does stage-gate G02** through `platform/check_gate_g02_specification.py`. That gate confirms the required authority files and structural population tokens; it does not replace this semantic review or approve the S2-01 SAP/TFL decision.

**Next engineering:** strengthen the G02 machine check so it asserts the endpoint-ID tokens and the explicit S2-01 disclosure whenever this pack changes.

---

## 8. Review agenda (Spec workstream, 45 min)

1. Walk populations table—challenge any TFL that violates SAFFL/ITT rules.  
2. Walk endpoints—confirm each controlled TFL maps here.  
3. Read the Section 2 audit, F-012, and the S2-01/S2-02 decisions.
4. Approve or reject any proposed catalog promotion or SAP amendment.

---

## 9. Exit criteria for WS-2 GREEN (Path A)

- [x] Populations named with flags  
- [x] Controlled endpoints mapped to TFL IDs  
- [x] Deferred set pointed to catalog  
- [x] F-011 closure and F-012 limitation linked
- [x] Section 2 review note filed
- [x] Runtime G02 gate exists
- [ ] ED-01–ED-07 adopted by the accountable author with limitation acknowledgement, then SAP-native `T-11-3`–`T-11-8` mapping implemented/resealed

Board status: **AMBER** until the T-11-8 decision and the Section 3 endpoint-origin/diary handoff are closed.
