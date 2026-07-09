# Meta-Audit — Path A Work to Date (pre W-ADAM-01)

**Date:** 2026-07-09  
**Scope:** Everything claimed/done from portfolio surface through SDTM E2E and ADaM dens — **before** dual-lang rebuild  
**Method:** Re-read packs + re-verify source facts on local XPTs + `verify_release` + m5 drift + CI  
**Verdict:** **Path A claim holds.** Science dens mostly correct. **Three honesty gaps** before calling package/code “in sync.”

---

## 0. Executive scorecard

| Area | Grade | One line |
|---|---|---|
| Product claim / dual surface | **PASS** | Path A frozen; non-claims clear |
| CI / seal recheck | **PASS** | `verify_release` **25/25**; latest CI green on dens commit |
| SDTM E2E | **PASS (dispositioned)** | GO ADaM; F-028/scope/AE dens disclosed |
| CRF grounding D-012 | **PASS** | Core domains grounded; Path B aCRF deferred |
| ADaM arm authority (code) | **PASS (factory)** | DM.ARM map in factory ADSL SAS/R |
| ADaM dens (XPT facts) | **PASS** | ADTTE/ADEX/ADAE dens rules hold on prod XPT |
| ORR dens (TFL source) | **PASS** | Left-join MEAS=203; display already 13/203 |
| Dual-lang seal currency | **FAIL → OPEN** | No rebuild after arm-map code (W-ADAM-01) |
| m5 review-package programs | **FAIL** | Git-tracked m5 programs **drift** vs factory |
| Register / board currency | **PARTIAL** | Dens pack current; board rows lag slightly |
| Filing-grade SDTM/ADaM | **N/A (Path A)** | Correctly not claimed |

**Overall:** Safe to **hold Path A** or proceed to **W-ADAM-01**. Not safe to claim “package programs match factory” or “seals cover post-arm-map code.”

---

## 1. What we actually did (timeline of value)

| Commit / pack | Workstream | Substance |
|---|---|---|
| Portfolio + git surface | WS-0/7 | Dual surface; only standard artifacts in git |
| G00/G02/G07 + seals | WS-7 | Executable gates; demo RC seals |
| CI `path-a-seal-verify` | WS-7 | Data-free CI green |
| WS-6 ADRG/SDRG/BDRG | WS-6 | Path A honesty in guides |
| CORE residual matrix | WS-1/3/5 | F-015 disposition, no greenwash |
| D-012 CRF grounding | WS-1 | AE/LB/ECOG/DS form↔extract |
| AE baseline skeleton + soft AESER QC | WS-4 | F-026 path |
| SDTM E2E audit | WS-1 | GO ADaM; F-028; 18 vs 34 scope |
| ADaM phase entry | WS-4 | DM arm map code; TEAE=TRTEMFL dens rules |
| ADaM dens audit | WS-4 | ADTTE/ADRS/ADEX contracts; ORR left-join fix |

Tip: `fbcad07` · branch `main` clean · origin synced.

---

## 2. Re-verification (live facts, this audit)

### 2.1 Source / SDTM

| Check | Result |
|---|---|
| DM N / ARM | **371** all `MITOXANTRONE/PREDNISONE` |
| F-028 EXTRT | MITOX 1731 · PRED 1241 · PREDNISOLONE 503 · **XRP6258 = 10** (1 subj) — **CONFIRMED** |
| Package define_sdtm ItemGroups | **18** |
| Local m5 SDTM XPT count | **18** (patient XPT gitignored — correct policy) |
| SDRG F-028 + scope language | Present |

### 2.2 ADaM dens (prod XPT)

| Check | Result |
|---|---|
| ADSL ITT/SAF/MEAS / TRT01P | 371 / 371 / 203 / all MP |
| ADTTE dens | OS/PFS/TTPSA/TTPAIN/TTSAE=371; TTUMOR=203 |
| ADRS full-spine | PSARESP/PSPROG/BSGRESP=371 |
| ADRS BOR/OBJRESP | 351 (spine ≠ ORR dens) |
| MEAS without OBJRESP | **2** |
| ADEX n_subj | 371 |
| ADAE subjects / TEAE / SAF no AE | 357 / 328 / **14** |
| TEAE blank AESER rows | **1** (soft QC; hard gate OPEN) |

### 2.3 TFL published numbers

| Output | Observation |
|---|---|
| T-11 ORR MP | **13/203 (6.4%)** — dens footnote correct |
| T-11-8b response-evaluable | 13/351 — honest alternate dens |
| T-20 TEAE MP | 328 (88%) on **N=371** — dens correct |

ORR Fisher path in **factory** `tfl_generation.R` now left-joins MEAS (was OBJRESP∩MEAS=201). **Published table N was already 203**; rate unchanged (missing → N). Full TFL re-run not required for dens N on T-11 face, but two-arm Fisher p may still reflect last sealed render.

### 2.4 Seals / CI

| Check | Result |
|---|---|
| `python3 scripts/verify_release.py` | **25/25 PASS** |
| pipeline_health | GREEN · full_dag · oda |
| Latest CI on dens commit | **success** |
| Seal meaning | Rechecks **prior** sealed JSON grades — **not** proof post-arm-map code was re-executed |

### 2.5 Code vs package drift (**material**)

| File | Factory | m5 (git-tracked review copy) |
|---|---|---|
| `A_adsl_generation.sas` | DM.ARM → TRT01P map | **Still config constant** `TRT01P_CODE` |
| `v_adsl_validation.R` | DM arm map | **Drifted** (old) |
| `A_adtte` / `A_adrs` / `A_adex` dens headers | Present | **Drifted** |
| `tfl_generation.R` ORR left-join | Present | **Drifted** |
| `A_adae_io_respec.sas` dens/TEAE notes | Present | **Drifted** |

**Finding M-01 (Major process):** Review-package programs in `08_submission_package/m5/.../programs/` **do not match factory** after ADaM entry + dens commits. Interviewer opening m5 sees **pre-arm-map** ADSL code.

XPT outcome risk for Path A MP-only: **low** (all DM MITOX → map and config constant both yield TRT01P=MP). Honesty risk: **high**.

### 2.6 XPT rebuild lag

| Artifact | Evidence |
|---|---|
| `adsl_prod.xpt` mtime | ~20:28 local (pre 23:44 arm-map commit) |
| Arm map code | `61d17f7` |
| Dens contracts | `fbcad07` |

**Finding M-02:** Production XPTs **not regenerated** after ADSL arm authority change. Values still valid for MP Path A; seals claim prior dual-lang recon, not this code path.

---

## 3. Claim honesty map

| Allowed claim (PRODUCT_CLAIM) | Still true? |
|---|---|
| Controlled non-submission biometrics demo | **YES** |
| SDTM→ADaM→TFL→Define→eCTD-style control | **YES** |
| Dual-lang recon on real MP under genuine SAS (sealed run) | **YES for sealed historical run** |
| Hash-sealed demo RC | **YES** |
| Not FDA filing / not P21-clean / not GxP org DP | **YES** (still must not claim) |

| Easy overclaim after this work | Counter |
|---|---|
| “We fixed arm authority end-to-end in the package” | m5 programs still old; no rebuild |
| “ORR dens bug was wrong in published tables” | Published T-11 already 13/203 |
| “SDTM fully clean” | CORE residuals + F-028 accepted |
| “All ADaM dens fixed in datasets” | OBJRESP still BOR spine; dens at TFL for ORR |

---

## 4. Work item status (truth table)

| ID | Register says | Audit confirms |
|---|---|---|
| W-SDTM-01 F-028 disclose | Done via pack/SDRG | **YES** |
| W-SDTM-02 dens N=371 | Verified in ADaM section | **YES** (T-20 + XPT); SDTM table exit text slightly stale |
| W-SDTM-03 18 vs 34 | Done in E2E | **YES** |
| W-ADAM-00 entry | PASS | **PASS factory**; m5 lag |
| W-ADAM-01 rebuild | OPEN | **Still OPEN — confirmed necessary for honesty** |
| W-ADAM-02 AESER hard gate | OPEN | **1 TEAE blank AESER** — soft only |
| W-ADAM-03/04 dens | DONE | **YES** |
| W-ADAM-05 OBJRESP full MEAS | Open optional | Correct residual |
| W-PKG-01 PDF refresh | Optional | Still optional |
| **M-01 m5 program sync** | Not previously ID’d | **NEW — must track** |

---

## 5. What was *not* over-claimed (good discipline)

- No silent EXTRT re-code  
- No invented AE for 14 zero-AE subjects  
- No full-domain SDTM dump claim  
- No commercial P21 clean  
- CbzP remains TFL-only synthetic  
- Dual-lang independence disclosed as single-author bounded  

---

## 6. Residual board (pre-rebuild)

| Pri | ID | Action |
|---|---|---|
| **P0** | **W-ADAM-01** | Dual-lang rebuild + recon after arm map (when ODA) |
| **P0** | **W-PKG-02** (new) | Re-materialize / sync **m5 programs** from factory (even without XPT in git) so review surface matches source |
| **P1** | **W-ADAM-02** | Hard-fail TEAE blank AESER after rebuild |
| **P2** | Register hygiene | Mark W-SDTM-02 exit complete in SDTM table; refresh WORKSTREAM board “done recently” for dens |
| **P2** | W-ADAM-05 | Only if SAP wants OBJRESP dens = MEAS in ADaM |
| **P3** | W-PKG-01 | Guide PDF re-package |

---

## 7. GO / NO-GO next steps

| Question | Answer |
|---|---|
| Hold Path A interview as-is? | **GO** with honesty: dens/F-028 packs; seal = last ODA full DAG; factory has newer arm/dens code than m5 |
| Run W-ADAM-01 rebuild now? | **GO** when engine available — closes M-02 |
| Sync m5 programs without rebuild? | **GO now** — closes M-01 for program face (data still old seals) |
| Claim dens slice fully sealed? | **NO-GO** until rebuild + optional TFL re-render + re-seal |
| Expand to Path B? | **NO-GO** without PRODUCT_CLAIM amendment |

---

## 8. Bottom line

We did real principal work: **claim freeze, CI seals, CRF grounding, SDTM E2E with F-028, ADaM dens contracts, ORR dens code fix, TEAE dens honesty.**  

We did **not** yet: **re-execute dual-lang**, **sync m5 programs**, or **promote soft AESER QC**.  

Those three are the gap between “audited and programmed correctly in factory” and “package + seals tell the same story.”
