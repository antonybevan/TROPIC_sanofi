# WS-2 Population & Endpoint Control Table

**Workstream:** Statistical Specification (G02)  
**Product claim:** Path A  
**As of:** 2026-08-09
**Authorities:** SAP v4.0 · `config/study_config.yaml` · `config/tfl_output_catalog.yaml` · ADRG · [Section 2 audit](../../06_qc_evidence/audit/section_reviews/SECTION_02_POPULATIONS_ENDPOINTS_AUDIT_2026-08-03.md)

**Decision handoff:** The F-042 accountable-author review packet and [F-042 / T-11-8 Endpoint Decision Record](decisions/ENDPOINT_DECISION_RECORD_F042_T11_8_2026-08-03.md) record Antony Bevan's 2026-08-04 adoption of ED-01–ED-07 as written. Phase 2 implementation is now present in separate SAS and R tracks under the [approval specification](decisions/F042_ENDPOINT_APPROVAL_SPEC_2026-08-03.md), [quantified impact appendix](decisions/F042_PFS_PAIN_IMPACT_APPENDIX_2026-08-03.md), and [CM/PR source qualification audit](decisions/F042_PR_SOURCE_QUALIFICATION_AUDIT_2026-08-03.md). The expanded 37-stage real-SAS rerun, delayed second-pass review, and pipeline release seal are complete for Path A; Git review/commit/tag remains a separate governance step. No independent, sponsor, or regulated approval is claimed.

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
| **ITT** | `ITTFL='Y'` | ADSL → carried to ADTTE | OS, PFS, TTPSA, TTUMOR and TTPAIN | MP N=371; synthetic CbzP N=378; combined N=749 is not protocol ITT N=755. |
| **Safety** | `SAFFL='Y'` | ADSL | ADAE TEAE tables T-20; lab shifts T-21; exposure | MP N=371; synthetic CbzP N=371. Denominators use SAFFL, not AE-distinct N. |
| **Measurable disease** | `MEASDISF='Y'` | ADSL | ORR response summary; TTUMOR supportive subgroup/sensitivity | ORR dens = **all** MEAS subjects left-join ADRS OBJRESP: MP N=203, CbzP N=179. TTUMOR primary is now ITT; MEAS remains supportive. |
| **Package combined display** | Real MP + synthetic CbzP | TFL merge only | Comparative figures/tables | **Not** protocol ITT 755 (F-012) |
| **PSA response analysis set** | `PSARESP` rows joined to ADSL baseline PSA, excluding controlled fallback (`PSABLIF='Y'`), and filtered `PSABL >= 20` | ADRS + ADSL | PSA response in the current T-11 response block and F-13-1 | **F-011 resolved:** MP 61/329; CbzP 145/361; 690 unique eligible subjects. Synthetic rows without `PSABLIF` are treated as observed. |
| **Pain progression** | ADTTE `PARAMCD='TTPAIN'`; ED-01–ED-03/ED-07 CM+PR-qualified, component-specific rule | ADTTE | T-11-8 | SAP assigns TTPAIN to T-11-8. The implemented rule uses component-specific summaries, same-component confirmation, the SV date hierarchy, direct-intent CM+PR union, diary/RT lineages and bounded date sensitivity. |

### Population hard rules

1. Never label N=749 as original-trial ITT.  
2. Safety tables: safety N from ADSL SAFFL by arm.  
3. MP-only recon ADaM remains the dual-lang truth set.

---

## 3. Endpoints & parameters (controlled)

| Endpoint / param | PARAMCD / measure | Population | Primary ADaM | Controlled TFL IDs | Config / SAP hooks |
|---|---|---|---|---|---|
| Overall survival | OS | ITT | ADTTE | F-11-1, forest F-12-1 | Results recon LIFETEST; randomization origin |
| Progression-free survival | PFS (typed lesion-derived tumour / reconstructed PSA / governed pain / death composite + earlier NACT censor) | ITT | ADTTE | F-11-2 | Randomization origin; `BSGRESP` and `CLINPROG` are explicitly excluded |
| Time to tumor progression | TTUMOR | ITT primary; `MEASDISF='Y'` supportive subgroup/sensitivity | ADTTE | T-11-6 | Protocol/publication and SAP Table 22 support ITT. The reconstructed CbzP arm now carries one record per ITT subject; ORR retains the measurable-disease denominator. |
| Time to PSA progression | TTPSA | ITT | ADTTE | T-11-7 | Physical block and index agree; current CbzP parameter is PH-scaled demonstration data. |
| Time to pain progression | TTPAIN | ITT with ED-01–ED-03/ED-07 qualification | ADTTE | T-11-8 | Start is randomization; primary diary/RT evidence and diary-only, RT-only, and date-bound supporting lineages are retained. |
| PSA response | PSARESP | Observed ADSL baseline PSA >=20 (`PSABLIF != 'Y'`) plus unique PSARESP row | ADRS + ADSL | T-11-3 | F-011 resolved: MP 61/329; CbzP 145/361. |
| Objective response | OBJRESP | MEAS TFL dens; ADRS row = confirmed lesion-derived response spine | ADRS + TFL left-join | T-11-4; response-evaluable T-11-8b sensitivity | MEAS dens MP 203/CbzP 179; response-evaluable spine MP 185/CbzP 378. Current MP results: 12/203 primary and 12/185 sensitivity. |
| Pain response | PN/SV-derived response event | ITT PAINBL='Y' with evaluable baseline and consecutive assessment | F-042 event evidence + TFL | T-11-5 | Real MP 43/156 (27.6%); CbzP is explicitly N/A because PN is unavailable in the synthetic arm. |
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
| `BONE_PROG_*` | Exploratory 2+2 bone-scan demonstration in ADRS; non-TTE |
| Lab windows `W_*` | ADLB analysis visits |
| `AGE_STRAT_CUT` | Subgroup forest |

---

## 4. Deferred endpoints / displays (not Path A deliverables)

All IDs in `config/tfl_output_catalog.yaml` marked `deferred_not_in_scope` (18 SAP full-catalog IDs) remain outside the controlled release. The promoted T-11-3, T-11-4, and T-11-5 response outputs are no longer deferred; the catalog itself is authoritative for the remaining IDs.

**Programming must not silently implement these without:**

1. Catalog promotion (in-scope + disposition)  
2. Shell / SAP basis  
3. QC plan entry in validation_strategy  

---

## 5. SAP/TFL alignment note

The adopted Path A implementation restores the SAP-native `T-11-3` PSA response, `T-11-4` ORR, `T-11-5` pain response, `T-11-6` TTUMOR, `T-11-7` TTPSA and `T-11-8` TTPAIN mapping. The T-11-8 collision is therefore resolved/mapping restored in the controlled catalog, physical table block, CTQ register, ARM/ARS and reviewer guides; `T-11-8b` remains an explicitly labelled ORR response-evaluable sensitivity. Primary PSA/ORR results do not require an invented extension ID. The completed full-DAG rerun, release reseal and CI verification are the controlling evidence of the implementation state.

## 6. Estimand posture (honest)

Path A demonstrates **implementation of endpoint algorithms** suitable for a programming portfolio.  
It does **not** deliver a full ICH E9(R1) estimand package for filing (intercurrent events strategy documentation remains lightweight relative to a sponsor SAP).

CTQ register: `config/ctq_traceability.yaml` + `docs/CTQ_TRACEABILITY_REPORT.md`.

---

## 7. G02 gap acknowledgment

The orchestrator **does stage-gate G02** through `platform/check_gate_g02_specification.py`. The gate now checks the ITT/MEAS distinction and the restored SAP-native endpoint-ID semantics (`T-11-3` through `T-11-8`) in both this table and the controlled catalog; it does not replace independent clinical/statistical review or approve a regulated filing.

**Next engineering:** maintain the G02 machine check so it asserts the endpoint-ID tokens and the explicit S2-01 disclosure whenever this pack changes.

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
- [x] ED-01–ED-07 adopted by Antony Bevan with single-author limitation acknowledgement
- [x] SAP-native `T-11-3`–`T-11-8` mapping implemented in code, catalog, metadata and reviewer guides
- [x] TTUMOR ITT primary and CM+PR-qualified pain derivation implemented in separate SAS/R tracks
- [x] Full 37-stage real-SAS DAG, delayed second-pass review and pipeline release seal recorded for this change set
- [x] T-11-5 same-component maintenance corrected in SAS and a subject-level SAS/R endpoint gate made release-blocking

Board status: **GREEN for Path A only when the current machine evidence satisfies the
[statistical governance assessment](reviews/PATH_A_STATISTICAL_GOVERNANCE_ASSESSMENT_2026-08-04.md)
conditions**, including `endpoint_controls.F042_PAIN_RESPONSE=PASS`. External
qualified review remains required before regulated reuse.
