# WS-4 ADaM Denominator Audit (W-ADAM-03 / W-ADAM-04)

**Date:** 2026-07-09  
**Scope:** ADTTE, ADRS, ADEX, ADAE/ADLB/ADCM dens + arm authority  
**Evidence:** Production XPTs under `04_analysis_datasets/adam/*_prod.xpt` (local, pre-rebuild seals)  
**Prior entry pack:** `WS4_ADAM_PHASE_ENTRY_2026-07-09.md`

---

## 1. Hard rules (reaffirmed)

| Rule | Path A requirement |
|---|---|
| Arm | `TRT01P` / treatment display from **ADSL ← DM**, never EXTRT (F-028) |
| Safety dens | **ADSL `SAFFL='Y'`** (N=371 MP); subjects with zero AE rows stay in dens |
| TEAE | **`TRTEMFL='Y'`** only |
| Measurable dens | **ADSL `MEASDISF='Y'`** for ORR TFL — not `nrow(OBJRESP)` |

---

## 2. Local XPT dens snapshot (MP only)

| Dataset | Check | Result | Status |
|---|---|---|---|
| **ADSL** | n / ITT / SAF / MEAS / TRT01P | 371 / 371 / 371 / 203 / all MP | **PASS** |
| **ADTTE OS** | n_subj == ITT | 371 match | **PASS** |
| **ADTTE PFS, TTPSA, TTPAIN** | n == 371 | 371 | **PASS** |
| **ADTTE TTSAE** | n == SAFFL | 371 | **PASS** |
| **ADTTE TTUMOR** | n == MEAS | 203 match | **PASS** |
| **ADTTE TRT01P** | unique values | MP only | **PASS** |
| **ADRS PSARESP / PSPROG / BSGRESP** | n_subj == SAFFL | 371 each | **PASS** |
| **ADRS OVRLRESP** | n_subj | 351 (lesion-evaluable spine) | **PASS** (by design) |
| **ADRS BESTRESP / OBJRESP** | n_subj | 351 (BOR spine) | **PASS** (by design) |
| **ADRS OBJRESP ∩ MEAS** | MEAS with OBJRESP row | 201 of 203 | **KNOWN** — 2 MEAS lack OBJRESP |
| **ORR TFL dens** | MEAS left-join OBJRESP | 203 dens; missing → N; 13 resp (6.4%) | **FIXED** in `tfl_generation.R` |
| **ADEX** | n_subj == SAFFL; TRT01P | 371 / MP | **PASS** |
| **ADAE** | n_subj with AE; SAFFL no AE | 357 with AE; **14** SAFFL with no AE row | **PASS** (dens at TFL) |
| **ADAE TEAE** | TRTEMFL=Y subjects | 328 / 371 | **PASS** (entry G-ADAM-06) |
| **ADLB** | n_subj; TRT01P | 371 / MP | **PASS** |
| **ADCM** | n_subj (OCCDS) | 371 | **PASS** |

### MEAS × OBJRESP cross-tab (why TFL dens ≠ OBJRESP n)

| MEASDISF | Has OBJRESP row | n |
|---|---|---|
| N | No | 18 |
| N | Yes | 150 |
| Y | No | **2** |
| Y | Yes | 201 |

- SAP / WS-2 ORR population = **MEASDISF='Y'** → dens **203**.  
- ADRS `OBJRESP` is built from the **BOR spine** (subjects with evaluable RECIST timepoints) → **351** rows, including 150 non-MEAS.  
- **Do not** use `filter(PARAMCD=="OBJRESP")` alone as ORR dens.  
- TFL now: `ADSL MEASDISF=='Y'` **left_join** OBJRESP; blank/missing AVALC → non-responder.

Two MEAS subjects without OBJRESP (both `DOCRESP=N`):  
`006193-480-808-501`, `006193-490-708-901`.

---

## 3. Code / contract changes this slice

| File | Change |
|---|---|
| `A_adtte_generation.sas` v2.5 | Dens contract header (ITT/SAF/MEAS by PARAMCD) |
| `v_adtte_validation.R` | Matching dens rule comments |
| `A_adrs_generation.sas` v2.1 | Dens contract: full-spine params vs BOR/OBJRESP spine; ORR dens at TFL |
| `v_adrs_validation.R` v2.1 | Same |
| `A_adex_generation.sas` v2.3 | SAFFL spine + ADSL arm dens note |
| `v_adex_validation.R` v2.1 | Same |
| `A_adlb_generation.sas` v2.2.1 | SAFFL dens note |
| `A_adcm_generation.sas` v2.2.1 | SAFFL dens note |
| `tfl_generation.R` | ORR Fisher + display dens = MEAS left-join OBJRESP; QC log line |

---

## 4. Gate results (this slice)

| Gate | Status | Notes |
|---|---|---|
| **G-ADAM-07** ADTTE dens by PARAMCD | **PASS** | OS/PFS/TTPSA/TTPAIN/TTSAE=371; TTUMOR=MEAS 203 |
| **G-ADAM-08** ADRS full-spine params | **PASS** | PSARESP/PSPROG/BSGRESP = 371 |
| **G-ADAM-09** ORR dens = MEAS left-join | **PASS** (code) | Was 201 (OBJRESP∩MEAS); now 203 |
| **G-ADAM-10** ADEX SAFFL dens + ADSL arm | **PASS** | 371/371; no EXTRT arm |
| **G-ADAM-11** Safety OCCDS dens at TFL | **PASS** | ADAE 14 zero-AE subjects retained in SAFFL dens |

---

## 5. Residual disposition

| ID | Work | Status after this slice |
|---|---|---|
| **W-ADAM-03** | ADTTE/ADRS dens audit | **DONE** — this pack |
| **W-ADAM-04** | ADEX dens/arm docs | **DONE** — headers + XPT verify |
| **W-ADAM-01** | Dual-lang rebuild after ADSL arm map | **OPEN** — needs SAS/ODA |
| **W-ADAM-02** | Hard-fail TEAE blank AESER | **OPEN** — soft QC only |
| **W-ADAM-05** | Optional: expand OBJRESP dens to full MEAS in ADaM (not only TFL) | **OPEN P2** — TFL dens is correct; ADaM spine remains BOR-evaluable by design |

---

## 6. Verdict

| Question | Answer |
|---|---|
| ADTTE dens correct for Path A? | **YES** |
| ADRS dens understood and ORR TFL fixed? | **YES** |
| ADEX dens/arm correct? | **YES** |
| Safe to claim dual-lang recon still sealed for new ADSL arm map? | **NO** until W-ADAM-01 rebuild |
| Block Path A demo? | **NO** — dens rules documented; ORR dens bug fixed in TFL source |

**Decision:** W-ADAM-03 / W-ADAM-04 closed. Next programming value is **W-ADAM-01** (rebuild) when engine available, else W-ADAM-02 or Path A hold.
