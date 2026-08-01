# TROPIC Workstream Execution Board

**Status:** Active operating board — not a decorative architecture map  
**As of:** 2026-07-09 (resume after portfolio surface)  
**Branch tip:** `codex/repo-structure-phase2` (presentation + git surface hygiene pushed)  
**Pipeline seal:** `v0.1.0-demo-rc.1` · release-run `PASS` · RC checklist `PASS` · `verify_release` 25/25  
**Product claim in force:** **Path A controlled non-submission demonstration** (`docs/PRODUCT_CLAIM.md`)  
**Authority:** SAP v4.0 remediation lock · `06_qc_evidence/audit/SAP_LOCK_REVIEW_MEMO.md` · `06_qc_evidence/audit/FINDINGS_DISPOSITION_BOARD.md`  
**Portfolio surface:** `docs/REPO_SURFACE_POLICY.md` · `docs/INTERVIEWER_GUIDE.md` · dual-surface README

---

## 0. Straight talk

We proved the **machine can enforce truth** (full DAG, dual-language recon, admiral, seals).  
That is **Release Engineering / platform** success.

We have **not** yet run this repository like a submission-style operating model where each function owns evidence, hands off through gates, and can be challenged in review.  
If we only keep sealing the DAG, this becomes a strong solo portfolio — not a career-grade submission operating system.

**This board is the correction.**  
Every workstream below is how we operate next. Reviews are **team by team**, not “one more green JSON.”

| Layer | What is true today |
|---|---|
| Platform / DAG | Green — do not re-litigate without a regression |
| Department evidence packs | Uneven — this board ranks the work |
| Submission-grade package | **Not claimed** — and must not be claimed until G00 product decision changes |

---

## 1. Operating rules

1. **No silent ownership.** Every artifact has a workstream owner below.  
2. **No decorative green.** A control file PASS without a human-readable pack is incomplete for that workstream.  
3. **Handoffs are gates G00–G09.** Downstream does not start a “promotion” claim until upstream gate is satisfied **or** explicitly waived with disposition.  
4. **ACCEPTED findings are residual risk owned by a workstream**, not trash.  
5. **One product claim at a time.** Demo RC vs submission simulation is a G00 decision; do not mix language.

---

## 2. Board legend

| Status | Meaning |
|---|---|
| **GREEN** | Evidence pack sufficient for current product claim; maintain |
| **AMBER** | Exists but incomplete for industry-style review of that function |
| **RED** | Blocks next product claim (submission simulation) or creates claim risk now |
| **WAIVED** | Out of scope for current demo claim; disposition on record |

---

## 3. Workstream execution rows

### WS-0 · Governance & Scope Control  
**Function:** What the package may claim · **Gates:** G00, G09 (claim side)

| Field | Content |
|---|---|
| **Owned artifacts** | SAP v4.0 · SAP lock memo · README · REPRODUCIBILITY · findings register · disposition board · release note · tag `v0.1.0-demo-rc.1` · product claim language |
| **Current status** | **GREEN** — `docs/PRODUCT_CLAIM.md` freezes the controlled demo claim and v0.2 submission-simulation path |
| **Open risks** | Language drift back to “submission-ready”; ACCEPTED Crits (F-003, F-005, F-025) misread as closed science |
| **Required evidence for GREEN** | `docs/PRODUCT_CLAIM.md` freezes demo vs submission simulation; disposition board linked from ADRG/SDRG (done for tag) |
| **Release gate** | G00 must hold before any new “submission simulation” language |
| **Next action** | Maintain claim language; next governance review only if G00 changes or public wording drifts |

---

### WS-1 · Clinical Data Management / Source Intake  
**Function:** Source truth, privacy, inventory · **Gate:** G01

| Field | Content |
|---|---|
| **Owned artifacts** | `01_source_data/` (governed, not redistributed) · staging ingest · SDTM validation · source profile report · SDTM CORE run records · SDRG source sections · F-017 timing residuals |
| **Current status** | **AMBER → improving** — pack + **CORE residual matrix filed**; F-015/F-017 dispositioned in CSV; still not “CORE clean” / commercial P21 |
| **Open risks** | F-017 remains source-inherent · F-015 open classes remain accepted · real SDTM not in git (correct) |
| **Required evidence pack** | (1) Source profile · (2) SDTM val · (3) CORE run record + **`WS1_CORE_RESIDUAL_MATRIX.csv`** · (4) SDRG §5.1 · (5) REPRODUCIBILITY data-access |
| **Release gate** | G01 before any “source locked” language |
| **Next action** | Maintain matrix on any CORE re-run; do not claim full CORE clean |

---

### WS-2 · Statistical Specification  
**Function:** Populations, endpoints, estimands · **Gate:** G02

| Field | Content |
|---|---|
| **Owned artifacts** | SAP v4.0 · `config/study_config.yaml` · CTQ/estimand register · ANALYSIS_REPORT · population rules (ITT/Safety/MEASDISF) · F-011 PSA denom residual |
| **Current status** | **AMBER** — config and SAP exist; G02 **is stage-gated** (executable); PSA eligibility shell residual (F-011) remains |
| **Open risks** | Spec drift from SAP; G02 never machine-checked; PSA / ITT wording inconsistency under review pressure |
| **Required evidence pack** | (1) Spec-to-config trace table · (2) Population/endpoint matrix · (3) Sensitivity list · (4) Explicit disposition of F-011 in ADRG + TFL footnotes if not coded |
| **Release gate** | G02 before claiming SAP-complete TFLs |
| **Next action** | Control table filed (`docs/workstreams/WS2_POPULATION_ENDPOINT_CONTROL.md`). **Next:** record one WS-2 review note; optional machine G02 check |

---

### WS-3 · Standards & Metadata  
**Function:** Spec → Define → CT → lineage · **Gate:** G03

| Field | Content |
|---|---|
| **Owned artifacts** | ADaM_spec.xlsx · define.xml · define_sdtm.xml · XSD validation · metadata lineage · metadata control report · ARM · Dataset-JSON / USDM / ARS (scope) · F-014/F-020/F-021/F-022 residuals |
| **Current status** | **AMBER** — metadata control PASS; lineage tools exist; ARM limited to controlled core; Dataset-JSON/USDM/ARS exploratory or partial |
| **Open risks** | Reviewer asks for full ARM/VLM/CT story; exploratory layers over-claimed; commercial P21 not run (F-016) |
| **Required evidence pack** | (1) Spec→define + spec→data status · (2) XSD validate run record · (3) Lineage check PASS · (4) Explicit “in package / exploratory” inventory for Dataset-JSON, USDM, ARS · (5) P21 slot: RUN or NOT_AVAILABLE with reason |
| **Release gate** | G03 before metadata promotion language |
| **Next action** | External validation index filed (`docs/workstreams/WS3_EXTERNAL_VALIDATION_EVIDENCE_INDEX.md`). **Next:** fill CORE residual matrix; keep P21 NOT_AVAILABLE until tool access |

---

### WS-4 · Statistical Programming (ADaM / BIMO / TFL)  
**Function:** Derivations and outputs · **Gates:** G04, G05

| Field | Content |
|---|---|
| **Owned artifacts** | SAS production + R validation programs · ADaM XPTs · BIMO clinsite · TFL suite · `config/tfl_output_catalog.yaml` · forest/results drivers · safety ADaM (ADAE/ADLB/ADEX) |
| **Current status** | **GREEN for demo claim** — dual-lang recon PASS; TFL controlled catalog PASS; admiral T1 in DAG PASS; safety programming present |
| **Open risks** | 21 deferred SAP TFL IDs; synthetic CbzP in TFLs; F-012 N=749 vs 755; manual SAS renderer remains diagnostic-only |
| **Required evidence pack** | (1) Program inventory by domain · (2) Catalog in-scope vs deferred · (3) Recon status JSON · (4) Admiral status · (5) TFL index + hashes · (6) Safety table list (T-20/T-21) |
| **Release gate** | G04/G05 — currently satisfied for controlled scope |
| **Next action** | **Do not expand scope casually.** Programming workstream review: walk ADSL → ADTTE → ADAE → T-20 with catalog and recon evidence only |

---

### WS-5 · QC / Validation  
**Function:** Challenge production · **Gate:** G06

| Field | Content |
|---|---|
| **Owned artifacts** | Risk-based validation plan · config/validation_strategy.yaml · recon (dataset/results/forest/admiral) · log cleanliness · findings register · disposition board · CORE local rules |
| **Current status** | **GREEN for Path A residual communication** — known-differences memo filed; machine gates PASS; still AMBER-leaning for industry if P21/CORE residual matrix missing (owned with WS-3) |
| **Open risks** | Single-author tracks; log coverage = persisted logs only; commercial P21 external |
| **Required evidence pack** | (1) Validation strategy control report · (2) Recon/admiral status · (3) Log cleanliness · (4) Findings + disposition · (5) **`docs/workstreams/WS5_KNOWN_DIFFERENCES_MEMO.md`** |
| **Release gate** | G06 |
| **Next action** | Hold residual memo current when any ACCEPTED finding changes; co-own CORE residual matrix with WS-1 |

---

### WS-6 · Regulatory Writing / Reviewer Explanation  
**Function:** Explain the package · **Gates:** G07 (primary), G08 narrative

| Field | Content |
|---|---|
| **Owned artifacts** | ADRG · SDRG · BDRG · TRACEABILITY_MATRIX · SDSP · ANALYSIS_REPORT · release note · limitation language · demo boundary |
| **Current status** | **GREEN for Path A narrative** — S1 ADRG + S2 SDRG + S3 BDRG/TRACEABILITY v1.1; G07 executable; optional PDF re-package lag only |
| **Open risks** | Package PDF copies may lag markdown until next `package_ectd`; over-claim if someone cites old PDFs only |
| **Required evidence pack** | (1) ADRG/SDRG/BDRG revision IDs · (2) Traceability matrix catalog-aligned · (3) is/is-not · (4) S1–S3 review notes |
| **Release gate** | G07 narrative satisfied for Path A; re-seal only if promotion-class science changes |
| **Next action** | Maintain guides on claim drift; optional package PDF refresh; hand residual matrix to WS-1 |

---

### WS-7 · Release Engineering / Platform  
**Function:** Prove the run · **Gates:** G08 (build), G09

| Field | Content |
|---|---|
| **Owned artifacts** | cibuild · study_manifest · renv.lock · delivery controls · evidence layers · release-run manifest · RC checklist · eCTD package/backbone · tag · CI |
| **Current status** | **GREEN for Path A release ops** — seals PASS; `scripts/verify_release.py` + `.sh`; **CI job `path-a-seal-verify`** + full-suite step |
| **Open risks** | Seal ≠ submission; EXAMPLE eCTD; CI does not re-run ODA (by design) |
| **Required evidence pack** | (1) pipeline_health · (2) release_run_manifest · (3) RC status · (4) tag · (5) release note · (6) CI `path-a-seal-verify` · (7) `scripts/verify_release.py` |
| **Release gate** | G09 — **PASS for demo RC** |
| **Next action** | Maintain seal allowlist; watch CI on PR to main; optional PDF re-package |

---

## 4. Cross-workstream handoff map (how departments would pass work)

```text
WS-0 Governance ──claim freeze──► all workstreams
WS-1 Source ──G01──► WS-2 Spec + WS-4 Programming
WS-2 Spec ──G02──► WS-3 Metadata + WS-4 Programming + WS-6 Writing
WS-3 Metadata ──G03──► WS-4 Programming + WS-5 QC
WS-4 Programming ──G04/G05──► WS-5 QC + WS-6 Writing
WS-5 QC ──G06──► WS-6 Writing + WS-7 Release
WS-6 Writing ──G07──► WS-7 Release
WS-7 Release ──G08/G09──► tagged package (v0.1.0-demo-rc.1 done for demo claim)
```

**Rule:** If you cannot name the upstream pack you consumed, you are not operating the model.

---

## 5. Priority queue (serious order — not “more automation for fun”)

| Priority | Workstream | Deliverable | Why |
|---:|---|---|---|
| **Done** | WS-0 | `docs/PRODUCT_CLAIM.md` | Stops claim drift; career protection |
| **P0** | WS-5 | Known-differences / residual risk memo for reviewers | Makes ACCEPTED findings usable in interview/review |
| **P1** | WS-6 | ADRG/SDRG/BDRG hardening against board + claim | Reviewer package is the human product |
| **P1** | WS-1 + WS-3 | External validation evidence index (CORE residual + P21 slot + XSD + eCTD validate) | Industry-grade package layer |
| **P2** | WS-2 | Spec/config/TFL control table | Closes G02 gap |
| **Done** | WS-7 | `verify_release` + CI `path-a-seal-verify` | Operational polish without reopening science |
| **P3** | WS-4 | Deferred TFL backlog only if claim expands | Do not explode scope on GREEN programming |

---

## 6. Review cadence (how we run this like departments)

1. **Weekly workstream review (one WS per session):** walk owned artifacts → status → risks → next action only.  
2. **No review without a pack list** (files + statuses).  
3. **G09 re-seal** only when a workstream changes promotion-class evidence (not for doc typos alone).  
4. **Tag policy:** new tag only when product claim or evidence grade changes (`v0.1.0-demo-rc.1` frozen).

---

## 7. What success looks like at the next milestone

Not “another GREEN JSON.”

**v0.2 workstream-operated demo package:**

- Every WS row is GREEN or WAIVED with pack file on disk  
- Known-differences memo complete  
- External validation index complete (RUN / NOT_AVAILABLE / residual)  
- ADRG/SDRG/BDRG read as controlled guides  
- `verify_release.sh` reproduces machine grades in one command  
- Product claim still honest  

**v1.0 submission simulation (only if G00 changes):**

- Real app metadata path, aCRF, Part 11 process evidence, CbzP claim resolved or removed  

---

## 8. Immediate next command (continue operating)

**Done recently:** portfolio surface · WS-6 guides · CORE matrix · CI green · **D-012 CRF grounding audit**  

**Next (optional polish):**

1. Re-package guide PDFs into `m5/` when convenient  
2. WS-2 review note if population/endpoint narrative drifts  
3. Extend CRF grounding to additional domains only if claimed in programming 

```bash
python3 scripts/verify_release.py   # local
# CI: job path-a-seal-verify + validate step "Path A release verification"
```
