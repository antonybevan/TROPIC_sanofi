# WS-2 Population & Endpoint Control Table

**Workstream:** Statistical Specification (G02)  
**Product claim:** Path A  
**As of:** 2026-08-03
**Authorities:** SAP v4.0 · `config/study_config.yaml` · `config/tfl_output_catalog.yaml` · ADRG · [Section 2 audit](../../06_qc_evidence/audit/section_reviews/SECTION_02_POPULATIONS_ENDPOINTS_AUDIT_2026-08-03.md)

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
| **ITT** | `ITTFL='Y'` | ADSL → carried to ADTTE | OS, PFS, TTPSA, and the endpoint-specific TTUMOR implementation | MP N=371; synthetic CbzP N=378; combined N=749 is not protocol ITT N=755. |
| **Safety** | `SAFFL='Y'` | ADSL | ADAE TEAE tables T-20; lab shifts T-21; exposure | MP N=371; synthetic CbzP N=371. Denominators use SAFFL, not AE-distinct N. |
| **Measurable disease** | `MEASDISF='Y'` | ADSL | ORR response summary; TTUMOR | Current TFL dens = **all** MEAS subjects left-join ADRS OBJRESP: MP N=203, CbzP N=179. Missing `OBJRESP` means non-responder; do not use the BOR spine (MP 351, CbzP 378). |
| **Package combined display** | Real MP + synthetic CbzP | TFL merge only | Comparative figures/tables | **Not** protocol ITT 755 (F-012) |
| **PSA response analysis set** | `PSARESP` rows joined to ADSL baseline PSA and filtered `PSABL >= 20` | ADRS + ADSL | PSA response in the current T-11 response block and F-13-1 | **F-011 resolved:** MP 61/330; CbzP 145/361; 691 unique eligible subjects. |
| **Pain progression** | ADTTE `PARAMCD='TTPAIN'` with diary evaluability | ADTTE | Not a separate controlled Path A TFL | SAP Appendix D assigns TTPAIN to T-11-8; the current response block uses that ID. This collision is recorded in the Section 2 audit and requires amendment or an extension-ID decision. |

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
| Time to tumor progression | TTUMOR | ITT ∩ `MEASDISF='Y'` in current implementation | ADTTE | T-11-6 | Physical block and index agree; SAP Table 22 says ITT and requires clarification. |
| Time to PSA progression | TTPSA | ITT | ADTTE | T-11-7 | Physical block and index agree; current CbzP parameter is PH-scaled demonstration data. |
| Time to pain progression | TTPAIN | ITT with diary evaluability | ADTTE | SAP target T-11-8; not currently controlled as a TFL | Five-of-seven diary rule is coded; palliative-RT/source-availability review is handed to Section 3. |
| PSA response | PSARESP | ADSL baseline PSA >=20 plus unique PSARESP row | ADRS + ADSL | Current T-11 response block; SAP-ID collision noted | F-011 resolved: MP 61/330; CbzP 145/361. |
| Objective response | OBJRESP | MEAS TFL dens; ADRS row = BOR spine | ADRS + TFL left-join | Current T-11 response block / response-evaluable sensitivity | MEAS dens MP 203/CbzP 179; response-evaluable spine MP 351/CbzP 378. |
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

The current Path A TFL text is internally reproducible, but `T-11-8` is not a valid SAP-ID mapping as presently written: SAP Appendix D/Table 22 defines it as TTPAIN, whereas the physical block is PSA response + ORR. This is an **open control decision**, not a hidden residual. Before a filing-facing rerun, either implement TTPAIN as T-11-8 and move the response summary to an approved extension ID, or amend the SAP/catalog and disposition TTPAIN explicitly. The Section 2 audit records the evidence and handoff.

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
- [ ] SAP T-11-8 collision resolved by amendment or explicit extension-ID decision

Board status: **AMBER** until the T-11-8 decision and the Section 3 endpoint-origin/diary handoff are closed.
