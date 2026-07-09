# WS-2 Population & Endpoint Control Table

**Workstream:** Statistical Specification (G02)  
**Product claim:** Path A  
**As of:** 2026-07-09  
**Authorities:** SAP v4.0 · `config/study_config.yaml` · `config/tfl_output_catalog.yaml` · ADRG  

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
| **ITT** | `ITTFL='Y'` | ADSL → carried to ADTTE | OS, PFS, TTPSA/TTUMOR per ADRG; efficacy TFLs | Randomisation-anchored for OS/PFS |
| **Safety** | `SAFFL='Y'` | ADSL | ADAE TEAE tables T-20; lab shifts T-21; exposure | Denominators for safety must use SAFFL N, not ITT alone |
| **Measurable disease** | `MEASDISF='Y'` | ADSL | ORR (T-11-8) | TFL dens = **all** MEAS subjects left-join ADRS OBJRESP (missing → non-responder). Do **not** use `nrow(OBJRESP)` (BOR spine 351 ≠ MEAS 203). See dens audit 2026-07-09. |
| **Package combined display** | Real MP + synthetic CbzP | TFL merge only | Comparative figures/tables | **Not** protocol ITT 755 (F-012) |
| **PSA response analysis set** | ADRS `PSARESP` rows (baseline + post-baseline PSA per ADRG) | ADRS | PSA response in T-11 | Stricter SAP shell deferred (F-011) |

### Population hard rules

1. Never label N=749 as original-trial ITT.  
2. Safety tables: safety N from ADSL SAFFL by arm.  
3. MP-only recon ADaM remains the dual-lang truth set.

---

## 3. Endpoints & parameters (controlled)

| Endpoint / param | PARAMCD / measure | Population | Primary ADaM | Controlled TFL IDs | Config / SAP hooks |
|---|---|---|---|---|---|
| Overall survival | OS | ITT | ADTTE | F-11-1, T-11 block, forest F-12-1 | Results recon LIFETEST |
| Progression-free survival | PFS (composite: tumour/PSA/pain/death + NACT censor) | ITT | ADTTE | F-11-2 | SAP v4 PFS hierarchy |
| Time to PSA progression | TTPSA | ITT (per ADRG) | ADTTE | T-11-6 | Secondary; CbzP PH-scaled if shown |
| Time to tumor progression | TTUMOR | ITT ∩ measurable where required | ADTTE | T-11-7 | |
| PSA response | PSARESP | PSA analysis set | ADRS | T-11-8 | F-011 residual on shell strictness |
| Objective response | OBJRESP | Measurable ITT dens at **TFL**; ADRS row = BOR spine | ADRS + TFL left-join | T-11-8 / T-11-8b | MEASDISF dens N=203; OBJRESP XPT n=351 |
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

## 5. Estimand posture (honest)

Path A demonstrates **implementation of endpoint algorithms** suitable for a programming portfolio.  
It does **not** deliver a full ICH E9(R1) estimand package for filing (intercurrent events strategy documentation remains lightweight relative to a sponsor SAP).

CTQ register: `config/ctq_traceability.yaml` + `docs/CTQ_TRACEABILITY_REPORT.md`.

---

## 6. G02 gap acknowledgment

Orchestrator **does not yet stage-gate G02**.  
Until a machine check exists, this control table + SAP + config are the G02 evidence pack.

**Next engineering (P2):** generate a machine check that every controlled TFL ID’s population/endpoint appears in this document’s YAML mirror (optional future `population_endpoint_control.yaml`).

---

## 7. Review agenda (Spec workstream, 45 min)

1. Walk populations table—challenge any TFL that violates SAFFL/ITT rules.  
2. Walk endpoints—confirm each controlled TFL maps here.  
3. Read F-011 and F-012 residuals.  
4. Approve or reject any proposed catalog promotion.

---

## 8. Exit criteria for WS-2 GREEN (Path A)

- [x] Populations named with flags  
- [x] Controlled endpoints mapped to TFL IDs  
- [x] Deferred set pointed to catalog  
- [x] Residuals F-011/F-012 linked  
- [ ] One recorded workstream review note  
- [ ] Optional: machine G02 check  

Board status: **AMBER** until review note filed.
