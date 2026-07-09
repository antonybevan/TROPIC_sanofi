# WS-4 ADaM Phase Entry Audit

**Date:** 2026-07-09  
**Entry criteria (from SDTM E2E):**  
1. Arm from **DM only** (not EXTRT)  
2. Safety dens from **ADSL SAFFL** (N=371 for MP; 14 no-AE subjects stay in dens)  
3. TEAE = **`TRTEMFL='Y'`** (not AESER non-missing)  
4. No EXTRT-based treatment arm  

**Verdict:** **Entry criteria implemented / verified** for Path A. Full dual-lang rebuild recommended when SAS/ODA available to refresh XPT seals.

---

## 1. Gate results

| Gate | Status | Evidence |
|---|---|---|
| **G-ADAM-01** Arm ≠ EXTRT | **PASS** | Grep: EXTRT only in SDTM validation / uplift / define — not ADSL/ADAE/TFL arm logic |
| **G-ADAM-02** TRT01P from DM | **FIXED → PASS** | Was config constant only; now **DM.ARM/ARMCD map** in `A_adsl_generation.sas` v2.4 + `v_adsl_validation.R` v3.6 |
| **G-ADAM-03** T-20 dens ADSL SAFFL | **PASS** | `tfl_generation.R`: `n_mp/n_cbzp` from `adsl$SAFFL` + `TRT01P`; TEAE filter `TRTEMFL=="Y"`; join arm from ADSL |
| **G-ADAM-04** TEAE definition | **PASS** | ADAE + T-20 use TRTEMFL; comment corrected (was wrong T/P/N) |
| **G-ADAM-05** ADSL n = DM n | **PASS** (local XPT) | adsl_prod n=371; QC notes added |
| **G-ADAM-06** TEAE subject count | **PASS** (local) | 328/371 TEAE (88.4%); 43 SAFFL with no TEAE — correct zero cells in dens |

---

## 2. Code changes this phase

| File | Change |
|---|---|
| `A_adsl_generation.sas` | DM.ARM/ARMCD → TRT01P/A; EX dates comment; ADSL-QC notes |
| `v_adsl_validation.R` | Same arm map; ADSL-QC notes |
| `tfl_generation.R` | T-20 comments: TRTEMFL Y/N; dens = ADSL SAFFL |
| `A_adae_io_respec.sas` | Comment: dens rule + TRTEMFL TEAE |

---

## 3. F-028 interaction

Subject with `EXTRT=XRP6258` still gets **TRT01P=MP** because **DM.ARM = MITOXANTRONE**.  
That is intentional Path A honesty: arm authority is DM; EX anomaly remains in SDTM (F-028 ACCEPTED).

---

## 4. Residual ADaM work (not blocking entry)

| ID | Work | Pri | Status |
|---|---|---|---|
| **W-ADAM-01** | Re-run dual-lang ADSL/ADAE + recon after this code change (ODA/local) | P0 when engine available | OPEN |
| **W-ADAM-02** | Hard-fail TEAE blank AESER after rebuild | P1 | OPEN |
| **W-ADAM-03** | Walk ADTTE/ADRS dens same ADSL rule | P1 | **DONE** — dens audit pack |
| **W-ADAM-04** | ADEX: document EX dates include all EXTRT; arm from ADSL | P2 | **DONE** |

**Dens follow-on:** `WS4_ADAM_DENS_AUDIT_2026-07-09.md` (G-ADAM-07–11).

---

## 5. GO / NO-GO deeper ADaM

| Question | Answer |
|---|---|
| Safe to continue ADTTE/ADRS/ADEX review under same rules? | **GO** — dens slice complete |
| Re-seal release without rebuild? | **No** — code changed; seal still prior XPT until full DAG |

Local verify_release still checks **prior** sealed XPT-derived grades — program changes do not invalidate Path A claim until next ODA seal cycle.
