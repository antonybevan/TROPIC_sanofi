# TROPIC Product Claim Decision

**Document ID:** PRODUCT_CLAIM
**Version:** 1.2
**Effective:** 2026-08-05
**Status:** FROZEN for tag train `v0.2.1-portfolio` and successors until amended
**Owner workstream:** WS-0 Governance & Scope Control (G00)
**Binding companions:** `06_qc_evidence/audit/SAP_LOCK_REVIEW_MEMO.md` · `06_qc_evidence/audit/FINDINGS_DISPOSITION_BOARD.md` · `docs/RELEASE_NOTE_v0.2.1-portfolio.md` · `docs/WORKSTREAM_EXECUTION_BOARD.md`
**Presentation entry:** root `README.md` · `docs/INTERVIEWER_GUIDE.md` · `08_submission_package/README.md` · `docs/INDEX.md`
**Git surface:** `docs/REPO_SURFACE_POLICY.md` (only review face + spine + seals in git — not factory noise)

**Factual amendment:** The manifest-driven pipeline currently records **34 stages** (previously described as 30). This corrects the stage count only; it does not expand the controlled output scope or change the Path A product boundary.

---

## 1. Why this document exists

This repository can look “submission-ready” from the outside: CDISC datasets, dual-language recon, Define-XML, eCTD tree, release seals. That appearance is dangerous for a career if the **product claim** is not frozen.

This file is the single answer to:

> **What is TROPIC allowed to claim in an interview, README, ADRG, or portfolio review?**

If a sentence contradicts this file, the sentence is wrong—not this file.

---

## 2. Active product claim (v0.2.1)

### Claim (allowed)

**TROPIC is a controlled, non-submission clinical biometrics programming demonstration package** for study EFC6193 / NCT00417079 that:

1. Implements an end-to-end **SDTM → ADaM → TFL → Define → eCTD-style** control system.
2. Enforces **dual-language (SAS 9.4 / R) reconciliation** on real MP-arm analysis datasets under a genuine SAS engine (`oda` / `local`).
3. Applies **risk-tiered third-engine admiral** re-derivation for ADSL and primary TTE (OS, PFS).
4. Runs a **manifest-driven 34-stage DAG** with machine gates (recon, TFL catalog, logs, seals).
5. Publishes a **hash-sealed release-run record** and **release-candidate checklist PASS** under the honesty boundary below.
6. Organizes work as **workstreams** (source, standards, programming, QC, writing, release)—not as a single script pile.

### Non-claims (forbidden without a new PRODUCT_CLAIM version)

| Forbidden claim | Why |
|---|---|
| “FDA submission ready” / “NDA package complete” | No sponsor approval, real app IDs, aCRF, full validator stack, Part 11 system |
| “Independent clinical re-analysis of TROPIC efficacy” | CbzP arm is synthetic/reconstructed; comparative results are non-confirmatory |
| “GxP double programming complete” | Single-author tracks; methodological independence ≠ organizational independence |
| “Part 11 compliant” | Hash seals and Git are not a validated system with e-signatures |
| “Full Pinnacle 21 / commercial ADaM conformance cleared” | Not run; local CORE rules + dual-lang are substitutes only |
| “Protocol ITT N=755 reproduced in package” | Package uses real MP N=371 (+ synthetic CbzP N=378 for TFL only) |

---

## 3. Product path options (decision tree)

| Path | Code name | When allowed | What changes |
|---|---|---|---|
| **A — Controlled demo release** | `demo-rc` | **ACTIVE now** | Current seals; synthetic CbzP disclosed; EXAMPLE eCTD |
| **B — Submission simulation** | `sub-sim` | Only after G00 amendment + new tag train | Real/placeholder app metadata policy, aCRF plan, Part 11 process evidence stubs, CbzP claim resolved or removed from comparative primary story |
| **C — True submission support** | `sub-real` | Outside this public repo’s data rights | Full two-arm IPD, sponsor SOPs, org double programming, commercial validators |

**Decision for this repository at v0.2.1:** **Path A only.**
Any public talk track, LinkedIn line, or interview answer must map to Path A unless PRODUCT_CLAIM is revised and re-tagged.

---

## 4. Authority stack (what wins conflicts)

1. **This PRODUCT_CLAIM** — what we may assert.
2. **SAP v4.0** (`02_specifications/sap/TROPIC_SAP_v4.0_industry_grade.docx`) — analysis intent for programming remediation (not sponsor-approved filing SAP).
3. **SAP lock memo** — SAP is programming authority; package is not submission-passed.
4. **`config/tfl_output_catalog.yaml`** — which outputs are in controlled release scope.
5. **`config/study_config.yaml` / `config/study_manifest.yaml`** — parameters and DAG structure.
6. **Machine seals** — whether the *run* of the controlled scope is green.
7. **ADRG/SDRG/BDRG** — how we explain (must not exceed 1–4).

If ADRG and PRODUCT_CLAIM disagree, **PRODUCT_CLAIM wins** until ADRG is fixed.

---

## 5. Data claims (non-negotiable)

| Arm | N | Nature | Where used |
|---|---:|---|---|
| **MP (mitoxantrone)** | 371 | Real de-identified SDTM (PDS/Sanofi 2013); not redistributed in git | ADaM recon, primary dual-lang truth |
| **CbzP (cabazitaxel)** | 378 | Synthetic/reconstructed (Guyot OS/PFS; PH-scaled secondaries; sampling elsewhere) | TFL comparative demonstration only |
| **Protocol ITT** | 755 | Published trial target | **Not** package ITT; do not label 749 as protocol ITT |

ADaM `*_prod.xpt` / `*_v.xpt` deliverables for recon are **MP-only**.
CbzP is merged at reporting under controlled disclosure.

---

## 6. Validation claims (what dual-lang means)

| Engine | Role | Independence type |
|---|---|---|
| SAS 9.4 production | Production ADaM | Production track |
| R validation | Independent re-derivation | Methodological (language/library) |
| admiral | T1 third track ADSL/OS/PFS | Methodological (pharmaverse library) |

**Allowed sentence:**
“Independent dual-language reconciliation under real SAS, plus admiral third-engine on critical core.”

**Forbidden sentence:**
“Two-programmer GxP double programming with organizational independence.”

Sim mode (`sas_execution_mode=sim`) zero-diff is **not** double-programming evidence. Only `oda`/`local` with provenance guard.

---

## 7. Output claims (TFL universe)

Controlled release scope is defined solely by **`config/tfl_output_catalog.yaml`**:

- **21** in-scope output IDs must exist and index clean.
- **18** SAP full-catalog IDs are **deferred** with reasons—not silent gaps.
- Listings: **none** in controlled scope (false L-01 removed).

Claiming “full SAP Appendix D TFL package” is **false** under Path A.

---

## 8. Package claims (eCTD)

| Element | Status under Path A |
|---|---|
| Module 5–style tree, co-located define, backbone/STF | Demonstrated |
| Application identifiers | **EXAMPLE / 000000** — not real |
| CRF PDF | **Source CRF present** (`Sanofi CRF Tropic.pdf` / package `blankcrf.pdf`) |
| Annotated CRF (aCRF) | **Not claimed** as full page-level SDTM annotation package (Path A) |
| FDA eCTD validator commercial pass | Not claimed |
| Patient XPT in git | Never |

---

## 9. Machine seal claims (what PASS means)

At tag `v0.2.1-portfolio` (and successive Path A seals):

| Seal | Meaning |
|---|---|
| `pipeline_health` GREEN + `full_dag` + `oda` | Full 34-stage DAG ran under real SAS |
| `release_run_manifest` PASS | Hash-bound inputs/programs/outputs/QC under clean material tree |
| `release_candidate` PASS | G01–G09 checklist items for **Path A** satisfied |
| `validation_strategy` PASS | Risk-tier checks against current evidence |

**PASS does not mean** residual ACCEPTED findings are gone. It means they are **dispositioned** and must remain disclosed.

---

## 10. Interview / portfolio talk track (use this)

> “I built a submission-**style** biometrics control system on public TROPIC data: dual-language ADaM recon under SAS ODA, admiral on critical endpoints, controlled TFL catalog, Define/eCTD packaging, and a workstream operating board. The package is explicitly a **controlled demonstration**, not a filing: the comparator arm is reconstructed, eCTD IDs are EXAMPLE, and findings are dispositioned rather than hidden. The release-candidate seal proves the **platform enforces truth**; the workstream board is how I run it like departments handing evidence.”

---

## 11. Amendment control

To change the product claim (e.g. Path B):

1. Update this file (new version, date, what changes).
2. Re-open G00 on the workstream board.
3. Update disposition board and residual memo.
4. New release note + tag train (e.g. `v0.3.0-…`).
5. Do **not** silently edit README badges or ADRG to over-claim.

---

## 12. Sign-off (repo authority)

| Role | Name / mark | Date |
|---|---|---|
| Product owner / programmer of record | Antony Bevan | 2026-07-09 |
| SAP remediation authority | SAP v4.0 + lock memo | 2026-06-25 |
| Machine seal reference | `v0.2.1-portfolio` / RC PASS | 2026-08-05 |

*Electronic wet-ink sponsor signatures are out of scope under Path A (see F-025).*
