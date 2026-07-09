# Open Work Register — Path A (post D-012)

**Purpose:** What a principal programmer still treats as **real work**, not “green JSON theater.”  
**As of:** 2026-07-09  
**Seals:** Path A demo RC can remain green while these are open if dispositioned.

---

## Active backlog

| ID | Pri | Owner | Work | Why it matters | Exit |
|---|---|---|---|---|---|
| **W-AE-01** | P0 | WS-4 / WS-5 | Baseline AE skeleton (blank AESER on ~1134 BASELINE rows) fully documented + TEAE AESER soft QC | Reviewer may count blank AESER as data quality failure; TEAE analysis must stay clean | ADRG §4B + ADAE `[ADAE-QC]` logs; optional hard gate after rebuild |
| **W-AE-02** | P1 | WS-4 / WS-6 | Grade 5 / fatal mapping vs CRF grade 1–4 labels | Avoid “grade 5 not on CRF” false challenge | Documented ADRG §4B |
| **W-LB-01** | P1 | WS-1 / WS-6 | ALB/LDH Class C (not on CRF lab panels; not in LB) | Stop wrong “PDS stripped albumin” story | Documented ADRG §5.1 + D-012 |
| **W-AE-03** | P2 | WS-1 / WS-5 | CORE AESER residual disposition stays honest | No greenwashing source | Residual matrix + no overwrite |
| **W-CRF-01** | P2 | WS-6 / WS-7 | Full aCRF + real app IDs | Filing simulation only | Path B PRODUCT_CLAIM |
| **W-PKG-01** | P3 | WS-7 | Re-package ADRG/SDRG/BDRG PDFs into `m5/` | Markdown is source of truth; PDFs lag | Optional `package_ectd` |
| **W-CI-01** | Done | WS-7 | Data-free CI green with portfolio surface | Done on `main` | CI success |

---

## Explicitly **not** next (unless claim expands)

- Expanding deferred TFL catalog  
- Inventing day-true AE dates  
- Filling blank AESER on baseline rows with guessed Y/N  
- Claiming commercial P21 clean  

---

## Priority order for next session

1. **W-AE-01** — if rebuilding ADAE soon, promote soft QC to gated assert after dual-lang recon  
2. **W-PKG-01** — PDF refresh if demoing package face  
3. Otherwise hold Path A and interview with D-012 + this register  

Source decision: `WS1_CRF_GROUNDING_D012_2026-07-09.md`
