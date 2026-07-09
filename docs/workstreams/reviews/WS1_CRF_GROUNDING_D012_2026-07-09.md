# Decision D-012 — CRF Grounding Audit (Principal Programmer)

**Date:** 2026-07-09  
**Owner:** WS-1 Source Intake · WS-4 Programming · WS-6 Writing  
**Product claim:** Path A  
**Trigger:** Promise of form-level CRF fidelity (not dictionary-only programming).  
**Source CRF:** `01_source_data/Sanofi CRF Tropic.pdf` (EFC6193 / XRP6258, FINAL 21-Nov-2006, 525 pages)  
**Package copy:** `08_submission_package/m5/.../sdtm/blankcrf.pdf`  
**PDS extract checked:** `01_source_data/real_sdtm/{ae,lb,vs,ds}.sas7bdat`

---

## 1. Decision

Programming and reviewer narrative for AE, LB, ECOG (VS), and DS must be **CRF-grounded**:

1. State what the **sponsor form collected**.  
2. State what the **PDS public extract retains**.  
3. Never imply “trial didn’t collect X” when the CRF shows X was on the form.  
4. When X is missing or reduced in PDS, classify as **extract/de-id reduction**, not study design thinness — **unless** the CRF itself never asked for it.

This audit was completed **now** as an explicit correction event (not buried in unrelated work).

---

## 2. Method

| Step | Action |
|---|---|
| 1 | Inventory AE/LB/VS/DS columns and non-null rates in PDS extract |
| 2 | Extract CRF text (`pdftotext`) and locate form modules |
| 3 | Map form items → SDTM variables |
| 4 | Propagate corrected language to SDRG, residual memo, program headers |

**Forms read (this session):**

| Form / module | CRF marker | Approx. page (footer) |
|---|---|---|
| Adverse Event Form | `O.1_AE_1` | e.g. Page 6/525 (template also repeats by visit) |
| Hematology | `LABH_1` | Page 24/525 |
| Biochemistry + Testosterone | `LABB_1` | Page 25/525 |
| PSA | PSA-1/2 | Page 25–26 area |
| ECOG Performance Status | VS panel | Page 27/525 |
| End of Study | `O.ENDST_1` | early section (~Page 5 area in extract) |
| End of Treatment | `O.ENDTT_2` | Page 267/525 |
| Prior anti-cancer (CM context) | discontinuation reason codes | Page 14–15 |

**Not claimed:** full page-by-page annotated CRF (aCRF) with define origins for every variable — that remains Path A non-claim. **Source CRF PDF exists and was used for domain grounding.**

---

## 3. Findings by domain

### 3.1 AE (Adverse Event Form `O.1_AE_1`)

| CRF captures | PDS AE extract | Classification |
|---|---|---|
| Diagnosis / term | `AETERM` / `AEDECOD` / `AEBODSYS` present | Collected → retained |
| Status (new / ongoing…) | `AEPATT` populated for majority | Collected → retained |
| Grade (form labels **1–4**) | `AETOXGR` 1–5; **n=25 grade 5** (fatal) | Collected; grade 5 aligns with outcome “Fatal” / death report, not form checkbox 5 on grade item |
| Relationship to study treatment (Y/N) | `AEREL` Y/N largely populated (~4292/5428) | Collected → **retained** (not stripped wholesale) |
| Action taken with study treatment (0–5 codes) | `AEACN` mapped text (DOSE NOT CHANGED, WITHDRAWN, …) | Collected → retained |
| Corrective treatment | `AECONTRT` Y/N | Collected → retained |
| Outcome (incl. Fatal) | `AEOUT` incl. FATAL | Collected → retained |
| Seriousness Y/N + criteria (death, life-threatening, hosp, disability, congenital, other important) | `AESER` Y/N + `AESDTH`/`AESLIFE`/`AESHOSP`/`AESDISAB`/`AESCONG`/`AESMIE` | Collected → **largely retained**; AESER blank on ~1137/5428 rows (incomplete/null, not “column absent”) |
| Full calendar start/end dates (day/month/year) | **Week offsets** `AESTWK`/`AEENWK` (±3.5 day) | **Precision reduced in public extract** (de-id / release design) |

**Principal conclusion (AE):**  
Do **not** claim “trial didn’t collect seriousness/causality/action.” The CRF did, and PDS **retains** those columns for most records.  
Do claim: **date precision** is reduced to week-level in the public extract; residual blank AESER rows are extract incompleteness / nulls, not absence of the concept.

### 3.2 LB (Hematology `LABH_1` / Biochemistry `LABB_1` / PSA)

| CRF tests (examples) | In PDS `LBTESTCD`? |
|---|---|
| WBC, RBC, Neutrophils, Eos, Baso, Mono, Lymph, Platelets, HGB | Yes (`WBC`,`RBC`,`NEUT`,`EOS`,`BASO`,`MONO`,`LYM`,`PLAT`,`HGB`) |
| Sodium, Potassium, AST, ALT, ALP, Bili, BUN/Urea, Creatinine, Glucose, Chloride, Bicarbonate | Yes (`SODIUM`,`K`,`AST`,`ALT`,`ALP`,`BILI`,`BUN`/`UREA`,`CREAT`,`GLUC`,`CL`,`BICARB`) |
| Testosterone | Yes (`TESTO` / related) |
| PSA | Yes (`PSA`) |

**Principal conclusion (LB):** Lab panel is **CRF-collected and present** in the extract. Electrolyte gap is **not** the TROPIC story (Na/K/Cl/bicarb are on CRF and in data). Residual lab limitations are windowing/analysis choices, not “labs never collected.”

### 3.3 ECOG (VS)

| CRF | PDS |
|---|---|
| ECOG Performance Status boxes **0–4** | `VSTESTCD=ECOG`; observed levels 0–4 (majority 0/1/2; rare 3/4) |
| Protocol eligibility ECOG 0–2 | Matches inclusion criterion text on CRF |

**Principal conclusion (ECOG):** Codes match form. Stratification 0–1 vs 2 is clinically coherent with CRF/protocol severity cut — not invented.

### 3.4 DS (End of Treatment / End of Study)

| CRF | PDS |
|---|---|
| EOT main reason: completed, lack of efficacy, progression, AE, compliance, LTFU, other, subject request | `DSCAT`/`DSSCAT`/`DSDECOD`/`DSTERM` include DISEASE PROGRESSION, ADVERSE EVENT, COMPLETED…, LOST TO FOLLOW-UP, SUBJECT'S REQUEST, DEATH, etc. |
| EOS reasons: completed follow-up, death, compliance, subject request, LTFU, other | Present as disposition / follow-up / death rows |
| Death form referenced | Death-related DS rows present |

**Principal conclusion (DS):** Discontinuation reasons are **not** “missing because trial didn’t collect.” They are on CRF and largely **present in PDS**. Programming must map/use them honestly; do not invent richer reasons than extract supports.

---

## 4. Taxonomy of limitations (use this language)

| Class | Definition | TROPIC examples |
|---|---|---|
| **A. CRF collected + PDS retained** | Safe to treat as source-collected | AESER/AEREL/AEACN for majority; LB panel; ECOG; DS reasons |
| **B. CRF collected + PDS reduced** | Precision or completeness cut in public release | AE calendar dates → week offsets; some AESER blanks |
| **C. CRF not collected** | True non-collection | (None major found for the audited safety lab electrolytes) |
| **D. Programming scope** | We chose not to analyze | Deferred TFLs; synthetic CbzP TFLs |
| **E. Package / eCTD identity** | Demo packaging | EXAMPLE app numbers; not full aCRF annotation package |

---

## 5. Actions taken

| Artifact | Change |
|---|---|
| This decision record | Filed |
| `07_reviewer_explanation/guides/SDRG.md` | New § CRF grounding |
| `docs/workstreams/WS5_KNOWN_DIFFERENCES_MEMO.md` | F-005 / precision language tightened |
| `docs/PRODUCT_CLAIM.md` | CRF vs aCRF wording precise |
| ADAE SAS/R program headers | CRF grounding note |
| ADSL SAS header (ECOG/DS source note) | Brief CRF note |

**Not done (out of scope for this commit):** inventing missing AESER values; re-deriving day-true AE dates; full define aCRF page origins; re-seal.

---

## 6. Interview / review one-liner

> “I ground AE/LB/ECOG/DS against the Sanofi CRF. Seriousness, causality, and action were collected and are largely in the PDS extract. What the public release reduced is mainly **date precision** (week offsets) and some nulls — not ‘the trial never collected safety seriousness.’ The package CRF is a source copy, not a full annotated aCRF.”

---

## 7. Real work found (not docs-only)

D-012 was **not** a no-op. After form×extract reconciliation, these are **open / tracked** engineering items:

| ID | Priority | Finding | Recommended work | Status |
|---|---|---|---|---|
| **W-AE-01** | **P0** | ~1,134 **BASELINE** AE rows have MedDRA terms but blank AESER/AEREL/AEOUT (skeleton prior-AE pattern). Almost all blank AESER are `TRTEMFL=N`. | Document in ADRG; TEAE analyses already exclude via TRTEMFL; log soft QC if TEAE AESER blank >5 | **In progress** — ADRG §4B + ADAE QC notes |
| **W-AE-02** | P1 | CRF grade item shows 1–4; extract has `AETOXGR=5` (n=25, all FATAL) | Document mapping fatal outcome → grade 5 in ADRG (done §4B); optional define codelist note | Documented |
| **W-LB-01** | P1 | **Albumin / LDH** not on CRF LABH/LABB panels and not in PDS LB | Confirm Class C; keep ALBBL/LDHBL as Assigned placeholders; stop implying “PDS stripped ALB/LDH if never on form” | Documented ADRG §5.1 |
| **W-AE-03** | P2 | CORE residual AESER consistency (historical CORE-000266) | Keep ACCEPTED with D-012 narrative; no silent overwrite of source | Open (no data rewrite) |
| **W-CRF-01** | P2 | Full aCRF page-level origins for define | Path B only | Deferred Path A |
| **W-CRF-02** | P2 | Extend CRF grounding to CM/EX/lesion forms | Only if programming claims expand | Backlog |

### Principal judgment

| Not a “science hole” | Is real residual / work |
|---|---|
| “Trial never collected AE seriousness” (false for TROPIC) | Baseline AE skeleton incompleteness must be **named** so TEAE rates aren’t misread |
| “Electrolytes missing from study” (false — on CRF and in LB) | ALB/LDH truly **not on these CRF panels** → placeholder labs stay Assigned |
| Need to invent day-true AE dates | Week-offset precision remains F-017 Class B |

**Next coding slice if we continue:** optional machine gate failing CI only if TEAE blank AESER exceeds cap after full dual-lang rebuild; optional SUPPAE/baseline-AE analysis flag for transparency in ADAE.
