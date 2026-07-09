# Open Work Register — Path A (post D-012)

**Purpose:** What a principal programmer still treats as **real work**, not “green JSON theater.”  
**As of:** 2026-07-09  
**Seals:** Path A demo RC can remain green while these are open if dispositioned.

---

## Active backlog

### SDTM layer (complete E2E audit first — 2026-07-09)

| ID | Pri | Owner | Work | Why it matters | Exit |
|---|---|---|---|---|---|
| **W-SDTM-01** | **P0** | WS-1/WS-6 | Disclose **F-028**: EXTRT=XRP6258 (1 subj, 10 rows) vs DM all MITOXANTRONE arm | Arm must not be taken from EXTRT | SDRG + audit pack; no silent re-code |
| **W-SDTM-02** | **P0** | WS-4 | ADaM: any-AE / safety dens use **ADSL N=371** (14 subj have no AE) | Wrong denominator if AE-distinct only | Verify in ADaM phase |
| **W-SDTM-03** | P1 | WS-1/WS-6 | Package = **18** analysis-scoped domains vs **34** PDS | Avoid “full SDTM dump” claim | SDRG scope table (done in E2E pack) |
| **W-SDTM-04** | P2 | WS-5 | Optional QC list EXTRT ∉ expected set | Catch arm/exposure drift | Listing or gate |
| **W-AE-01** | P0 | WS-4 / WS-5 | Baseline AE skeleton + TEAE AESER soft QC | TEAE cleanliness | ADRG §4B + ADAE QC (done soft) |
| **W-AE-02** | P1 | WS-4 / WS-6 | Grade 5 / fatal mapping vs CRF grade 1–4 labels | Documented ADRG §4B | Done docs |
| **W-LB-01** | P1 | WS-1 / WS-6 | ALB/LDH Class C | Documented ADRG §5.1 | Done docs |
| **W-AE-03** | P2 | WS-1 / WS-5 | CORE AESER residual | No overwrite | Residual matrix |
| **W-CRF-01** | P2 | WS-6 / WS-7 | Full aCRF + real app IDs | Path B | Deferred |
| **W-PKG-01** | P3 | WS-7 | Re-package guide PDFs into `m5/` | Optional | Optional |
| **W-CI-01** | Done | WS-7 | Data-free CI green | Done | CI success |

**SDTM E2E audit pack:** `docs/workstreams/reviews/WS1_SDTM_E2E_AUDIT_2026-07-09.md`  
**Verdict:** **GO to ADaM** with residuals dispositioned.

### ADaM phase entry (2026-07-09)

| ID | Pri | Work | Status |
|---|---|---|---|
| **W-ADAM-00** | P0 | Arm from DM; dens ADSL SAFFL; TEAE=TRTEMFL; no EXTRT arm | **PASS** — `WS4_ADAM_PHASE_ENTRY_2026-07-09.md` |
| **W-ADAM-01** | P0 | Dual-lang rebuild ADSL/ADAE + recon after arm map change | **OPEN** — when SAS/ODA available |
| **W-ADAM-02** | P1 | Hard gate TEAE blank AESER | Soft QC present |
| **W-ADAM-03** | P1 | ADTTE/ADRS dens audit same ADSL rule | **DONE** — `WS4_ADAM_DENS_AUDIT_2026-07-09.md` |
| **W-ADAM-04** | P2 | ADEX dens SAFFL + ADSL arm docs | **DONE** — dens audit pack |
| **W-ADAM-05** | P2 | Optional: OBJRESP dens = full MEAS in ADaM (now TFL-only) | Open; TFL dens correct |
| **W-SDTM-02** | P0 | Confirm dens ADSL N=371 | **Verified** T-20 + dens audit |

**Dens audit pack:** `docs/workstreams/reviews/WS4_ADAM_DENS_AUDIT_2026-07-09.md`  
**ORR dens fix:** `tfl_generation.R` left-joins ADSL `MEASDISF='Y'` to OBJRESP (203, not 201).

---

## Explicitly **not** next (unless claim expands)

- Expanding deferred TFL catalog  
- Inventing day-true AE dates  
- Filling blank AESER on baseline rows with guessed Y/N  
- Claiming commercial P21 clean  
- Expanding ADRS OBJRESP to full ITT in ADaM without SAP basis  

---

## Priority order for next session

1. **W-ADAM-01** — dual-lang rebuild when SAS/ODA available (seals post arm-map change)  
2. **W-ADAM-02** — promote TEAE AESER soft QC after rebuild  
3. **W-PKG-01** — PDF refresh if demoing package face  
4. Otherwise hold Path A with dens pack + D-012  

Source decision: `WS1_CRF_GROUNDING_D012_2026-07-09.md` · dens: `WS4_ADAM_DENS_AUDIT_2026-07-09.md`
