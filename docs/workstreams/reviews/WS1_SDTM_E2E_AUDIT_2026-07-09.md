# WS-1 SDTM End-to-End Audit (Principal)

**Date:** 2026-07-09  
**Scope:** Source SDTM (PDS) → CRF fidelity → uplift → package Module 5 tabulations  
**Product claim:** Path A  
**Companions:** D-012 CRF grounding · CORE residual matrix · SDRG  

**Verdict for Path A:** **GO to ADaM** with **open SDTM residuals dispositioned** (no silent science holes).  
**Not filing-ready SDTM.**

---

## 1. Scope map (what “SDTM” means here)

| Layer | What it is | Domains |
|---|---|---|
| **L0 — Pristine PDS source** | Local `01_source_data/real_sdtm/*.sas7bdat` | **34** files (parent + SUPP + trial design fragments) |
| **L1 — Analysis-scoped package** | Uplifted / packaged under `m5/.../tabulations/sdtm/` + `define_sdtm.xml` | **18** ItemGroupDefs: DM EX AE LB CM DS VS LS PN + SUPP* + TA TS |
| **L2 — Source present, not packaged** | In PDS, **not** in define_sdtm / package XPT set | CD CX EG IE MH PE PR SC SV TE TI TV + SUPPEG SUPPIE SUPPMH SUPPPE SUPPPR |

**Principal rule:** Package SDTM is an **analysis-scoped clinical package**, not a dump of every PDS domain. That must stay explicit in SDRG.

---

## 2. Source inventory (L0) — facts

| Domain | N | Subjects | Notes |
|---|---:|---:|---|
| DM | 371 | 371 | MP arm only (`ARM=MITOXANTRONE/PREDNISONE`); SEX=M all |
| AE | 5428 | **357** | **14 DM subjects have no AE rows** |
| LB | 80788 | 371 | Full coverage |
| EX | 3485 | 371 | See §4 EX anomaly |
| DS | 2842 | 371 | EOT/EOS/death/follow-up structure present |
| VS | 18388 | 371 | ECOG + vitals |
| CM | 24534 | 371 | Heavy SUPPCM |
| LS | 5774 | 371 | Lesions |
| PN | 26982 | **358** | **13 subjects no pain diary** |
| EG | 558 | **352** | ECG present in source, **not packaged** |
| MH | 2292 | 346 | Medical history source, **not packaged** |
| SV | 3930 | 371 | Visit structure source, **not packaged** |
| IE | 42 | 38 | Screen/eligibility fragment |
| TA | — | — | **Built at uplift** (not in pristine list as source file; package has TA) |

SUPP-- present for AE/CM/DM/DS/EX/LB/LS and others; package retains SUPP for define-declared set.

---

## 3. CRF grounding status (form × extract)

| Domain | CRF module | Status |
|---|---|---|
| DM | DEMOG_1 | Grounded (SEX/RACE on form; AGE via AGEGRP de-id) |
| AE | O.1_AE_1 | Grounded D-012; baseline skeleton F-026 |
| LB | LABH_1 / LABB_1 / PSA | Grounded; ALB/LDH Class C F-027 |
| VS/ECOG | VITAL_1 | Grounded |
| DS | O.ENDTT_2 / O.ENDST_1 | Grounded |
| EX | (exposure visit forms) | Present in extract; **arm mismatch residual** §4 |
| CM | Prior meds / concomitant | Source rich; package includes CM |
| LS / PN | Tumor / pain | Source + package |
| EG / MH / PE | ECG / MH / PE forms | **CRF + source exist; not in package define** — scope, not “no CRF” |

---

## 4. Material findings (work, not vibes)

### F-SDTM-01 / **F-028** — EX treatment name vs DM arm (Major)

| | |
|---|---|
| **Fact** | One subject (`006193-530-002-603`) has **10 EX rows `EXTRT=XRP6258`** (cabazitaxel code) while **DM.ARM = MITOXANTRONE/PREDNISONE** for all 371 |
| **Where** | Pristine EX **and** packaged `ex.xpt` |
| **Risk** | Safety/exposure rollups if someone filters EXTRT without ARM; arm-based analysis must use **DM.ARM / ADSL**, not EXTRT alone |
| **Disposition** | **ACCEPTED** Path A with disclosure — do **not** silently re-code EXTRT |
| **Work** | SDRG note; programming must treat DM arm as authority; optional QC listing of EXTRT∉{MITOXANTRONE,PREDNISONE,PREDNISOLONE} |

### F-SDTM-02 — AE subject coverage (Major → disclose)

| | |
|---|---|
| **Fact** | AE subjects **357 / 371**; 14 randomized subjects have **zero AE records** |
| **Risk** | “Any AE” rates if denominator wrong |
| **Disposition** | Disclose; TEAE rates use SAFFL/ITT with zeros for no-AE subjects correctly only if programs left-join ADSL |
| **Work** | Confirm ADAE/T-20 denominators from ADSL not AE-distinct subjects (ADaM phase) |

### F-SDTM-03 — Package domain scope (Major → disclose)

| | |
|---|---|
| **Fact** | **17 source domains** not in package define (EG, MH, PE, SV, …) |
| **Risk** | Reviewer assumes package = full SDTM database |
| **Disposition** | **Analysis-scoped package** by design (define 18 groups) |
| **Work** | SDRG § package scope table (this audit) |

### F-SDTM-04 — AGEGRP semantics (Minor)

| | |
|---|---|
| **Fact** | `AGEGRP` holds age-like integers (+ `>=85`), not classic age-band codes; uplift derives `AGE` |
| **Disposition** | Document as de-id age carrier (already uplift path) |

### F-SDTM-05 — Prior D-012 items remain open work

Baseline AE skeleton (F-026), week-offset dates (F-017), CORE residual matrix (F-015), ALB/LDH Class C (F-027).

### Not blocking (verified clean enough for Path A)

| Check | Result |
|---|---|
| DM N=371 unique | PASS |
| LB full subject coverage | PASS |
| AESER consistency when non-blank | PASS (Y always has criteria) |
| TEAE blank AESER | ~0–1 |
| define_sdtm ItemGroups vs package XPT | **Aligned 18** |
| TA/TS trial design in package | Present (uplift-enriched) |

---

## 5. Package / define checklist

| Check | Result |
|---|---|
| `define_sdtm.xml` ItemGroupDefs | 18 |
| Package `*.xpt` (excl. define/xsl) | 18 datasets |
| Co-located define + stylesheet + sdrg + blankcrf | Present |
| Uplift SDTMIG 3.4 | Declared; CORE residual matrix filed |
| Patient XPT in git | Present locally; git policy may track package xpt or not — data rights apply |

---

## 6. GO / NO-GO for ADaM phase

| Gate | Status |
|---|---|
| Source inventory known | **GO** |
| CRF grounding for core safety/efficacy inputs | **GO** (D-012 + this pack) |
| Package scope honesty | **GO** if SDRG updated |
| No silent re-code of EX anomaly | **GO** with F-028 ACCEPTED |
| Filing-grade full SDTM + aCRF | **NO-GO** (Path A by design) |

**Decision: proceed to ADaM** with SDTM residuals tracked; first ADaM checks must verify ADSL/ADAE denominators ignore EXTRT arm noise and zero-AE subjects correctly.

---

## 7. SDTM open work board (before/during ADaM)

| ID | Pri | Work | Owner |
|---|---|---|---|
| **W-SDTM-01** | P0 | Disclose F-028 EX XRP6258 vs DM arm in SDRG + OPEN_WORK | WS-1/WS-6 |
| **W-SDTM-02** | P0 | Confirm ADaM TEAE / any-AE denominators use ADSL N=371 | WS-4 |
| **W-SDTM-03** | P1 | Document package domain inclusion list vs L0 source | WS-1/WS-6 |
| **W-SDTM-04** | P2 | Optional QC listing: EXTRT not in expected set | WS-5 |
| **W-SDTM-05** | P2 | If Path B: consider packaging EG/MH/SV or explicit waiver | WS-0 |

---

## 8. What we will **not** do in SDTM phase

- Re-label subject 530-002-603 arm or EXTRT without sponsor source  
- Drop baseline AE skeleton rows from extract  
- Invent AE for 14 subjects without AE  
- Expand package to all 34 domains without define/control change  
