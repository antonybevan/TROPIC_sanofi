# TROPIC Workstream Execution Board

**Status:** Active operating board — not a decorative architecture map  
**As of:** 2026-08-24 (failed external-run evidence reconciled)
**Current candidate:** `v0.3.0-clinical-simulation` — **unreleased / NO-GO**; live telemetry is RED, `sim`, and `partial_dag`
**Latest tagged release:** `v0.2.2-portfolio` — immutable historical evidence, not the current candidate
**Evidence authority:** stage count/status come from `platform/pipeline_health.json`; promotion grade comes from `platform/release_run_manifest/release_run_manifest.json`, the RC checklist, and `scripts/verify_release.py`
**Current controls:** manifest defines 41 stages; complete test collection is enforced in CI; moving run/check counts are not duplicated on this board
**Product claim in force:** **controlled clinical-submission simulation; not a regulatory submission** (`docs/PRODUCT_CLAIM.md`)
**Authority:** SAP v4.0 remediation lock · `06_qc_evidence/audit/SAP_LOCK_REVIEW_MEMO.md` · `06_qc_evidence/audit/FINDINGS_DISPOSITION_BOARD.md`  
**Portfolio surface:** `docs/REPO_SURFACE_POLICY.md` · `docs/INTERVIEWER_GUIDE.md` · dual-surface README

> **Terminology note:** legacy “Path A” labels in the workstream rows mean the same
> controlled, non-submission portfolio boundary. They do not override the current
> product claim or authorize filing/readiness language.

---

## 0. Straight talk

The machine currently enforces the uncomfortable truth: the latest ODA handshake
failed, the fallback run is partial/simulated, and release promotion is blocked.
Prior genuine full-DAG evidence proves the workflow has run before; it is not the
current candidate state.

The workstream model is implemented. Reviews remain function-by-function, while
release authority always comes from the current telemetry, manifest, checklist,
and protected CI contexts—not from a manually copied GREEN narrative.

| Layer | What is true today |
|---|---|
| Platform / DAG | **RED for current promotion** — latest run is partial/simulated; retry genuine SAS/ODA |
| Department evidence packs | Implemented for the controlled scope; maintain and challenge residuals |
| Submission-grade package | **Not claimed** — and must not be claimed until G00 product decision changes |

---

## 1. Operating rules

1. **No silent ownership.** Every artifact has a workstream owner below.  
2. **No decorative green.** A control file PASS without a human-readable pack is incomplete for that workstream.  
3. **Handoffs are gates G00–G09.** Downstream does not start a “promotion” claim until upstream gate is satisfied **or** explicitly waived with disposition.  
4. **ACCEPTED findings are residual risk owned by a workstream**, not trash.  
5. **One product claim at a time.** The controlled-simulation/non-submission boundary is current; any filing-ready, validated-system, or regulated-use expansion requires a new G00 decision.

---

## 2. Board legend

| Status | Meaning |
|---|---|
| **GREEN** | Evidence pack sufficient for current product claim; maintain |
| **AMBER** | Exists but incomplete for industry-style review of that function |
| **RED** | Blocks the current candidate or a specifically proposed claim expansion |
| **WAIVED** | Outside the current controlled-simulation scope; disposition on record |

---

## 3. Workstream execution rows

### WS-0 · Governance & Scope Control  
**Function:** What the package may claim · **Gates:** G00, G09 (claim side)

| Field | Content |
|---|---|
| **Owned artifacts** | SAP v4.0 · SAP lock memo · README · REPRODUCIBILITY · findings register · disposition board · conditional v0.3.0 release note · product claim language |
| **Current status** | **GREEN** — `docs/PRODUCT_CLAIM.md` freezes the controlled-simulation/non-submission boundary; the v0.3.0 candidate remains unreleased until all promotion conditions pass |
| **Open risks** | Language drift back to “submission-ready”; ACCEPTED Crits (F-003, F-005, F-025) misread as closed science |
| **Required evidence for GREEN** | `docs/PRODUCT_CLAIM.md` freezes the controlled-simulation/non-submission boundary; disposition board is linked from ADRG/SDRG |
| **Release gate** | G00 must hold for the current candidate and before any filing-ready or regulated-use claim expansion |
| **Next action** | Maintain claim language; next governance review only if G00 changes or public wording drifts |

---

### WS-1 · Clinical Data Management / Source Intake  
**Function:** Source truth, privacy, inventory · **Gate:** G01

| Field | Content |
|---|---|
| **Owned artifacts** | `01_source_data/` (governed, not redistributed) · staging ingest · SDTM validation · source profile report · SDTM CORE run records · SDRG source sections · F-017 timing residuals |
| **Current status** | **GREEN for the controlled scope; AMBER for broader industry depth** — Section 1 source recheck passed; CORE residual matrix and F-015/F-017 dispositions are filed; still not “CORE clean” or licensed P21 Enterprise-cleared |
| **Open risks** | F-017 remains source-inherent · F-015 open classes remain accepted · real SDTM not in git (correct) |
| **Required evidence pack** | (1) Source profile · (2) SDTM val · (3) CORE run record + **`WS1_CORE_RESIDUAL_MATRIX.csv`** · (4) SDRG §5.1 · (5) REPRODUCIBILITY data-access |
| **Release gate** | G01 before any “source locked” language |
| **Next action** | Maintain matrix on any CORE re-run; hand off to Section 2; do not claim full CORE clean |

---

### WS-2 · Statistical Specification  
**Function:** Populations, endpoints, estimands · **Gate:** G02

| Field | Content |
|---|---|
| **Owned artifacts** | SAP v4.0 · `config/study_config.yaml` · CTQ/estimand register · ANALYSIS_REPORT · population rules (ITT/Safety/MEASDISF) · [Section 2 audit](../06_qc_evidence/audit/section_reviews/SECTION_02_POPULATIONS_ENDPOINTS_AUDIT_2026-08-03.md) |
| **Current status** | **CONDITIONAL GREEN for the controlled scope** — the statistical-governance review found and corrected `GOV-STAT-01`; current-head promotion requires exact T-11-5 subject-level SAS/R parity in addition to the full rerun/reseal |
| **Open risks** | Disclosed lack of independent sponsor/statistical/medical review; no filing-facing claim is authorized |
| **Required evidence pack** | (1) accountable-author review packet and decision record · (2) approval specification · (3) CM/PR source audit and sensitivities · (4) aggregate event-source evidence · (5) statistical governance assessment · (6) separately programmed SAS/R implementation, endpoint-level parity, delayed review, and full rerun/reseal |
| **Release gate** | G02 before claiming SAP-complete TFLs |
| **Next action** | Require `endpoint_controls.F042_PAIN_RESPONSE=PASS` on the current source tree; obtain external qualified statistical/medical review before any regulated reuse |

---

### WS-3 · Standards & Metadata  
**Function:** Spec → Define → CT → lineage · **Gate:** G03

| Field | Content |
|---|---|
| **Owned artifacts** | ADaM_spec.xlsx · define.xml · define_sdtm.xml · XSD validation · metadata lineage · metadata control report · ARM · Dataset-JSON / USDM / ARS (scope) · F-014/F-020/F-021/F-022 residuals |
| **Current status** | **GREEN for the controlled scope; AMBER for broader commercial-validator depth** — metadata control, lineage, XSD, spec→Define and spec→data pass; ARM covers every controlled analysis output except the non-analysis F-01-1 flow diagram (10 ResultDisplays / 18 AnalysisResults); Dataset-JSON/USDM/ARS remain explicitly exploratory or partial |
| **Open risks** | Reviewer asks for full ARM/VLM/CT story; exploratory layers over-claimed; Community has 30 open issue groups / 2,373 occurrences and a compatibility caveat; licensed Enterprise not run (F-016) |
| **Required evidence pack** | (1) Spec→define + spec→data status · (2) XSD validate run record · (3) Lineage check PASS · (4) Explicit “in package / exploratory” inventory for Dataset-JSON, USDM, ARS · (5) Community run record + self-reconciling aggregate inventory · (6) Enterprise slot explicitly NOT_AVAILABLE/NOT_EXECUTED |
| **Release gate** | G03 before metadata promotion language |
| **Next action** | Maintain the filed external-validation index and CORE residual matrix; retain Community as informative-only; require licensed, qualified Enterprise plus independent disposition approval for any regulated-use claim; require the G02 ARM semantic contract on every release |

---

### WS-4 · Statistical Programming (ADaM / BIMO / TFL)  
**Function:** Derivations and outputs · **Gates:** G04, G05

| Field | Content |
|---|---|
| **Owned artifacts** | SAS production + R validation programs · ADaM XPTs · BIMO clinsite · TFL suite · `config/tfl_output_catalog.yaml` · forest/results drivers · safety ADaM (ADAE/ADLB/ADEX) |
| **Current status** | **GREEN historical/program asset; RED current promotion** — controlled outputs and prior reconciliations exist, but the latest run did not complete genuine SAS/R or the downstream DAG |
| **Open risks** | 18 deferred SAP TFL IDs; synthetic CbzP in TFLs; F-012 N=749 vs 755; manual SAS renderer remains diagnostic-only |
| **Required evidence pack** | (1) Program inventory by domain · (2) Catalog in-scope vs deferred · (3) Recon status JSON · (4) Admiral status · (5) TFL index + hashes · (6) Safety table list (T-20/T-21) |
| **Release gate** | G04/G05 — not satisfied for the current candidate until a genuine full-DAG rerun refreshes same-run evidence |
| **Next action** | Retry genuine SAS/ODA in the governed window, then walk ADSL → ADTTE → ADAE → T-20 with current-run catalog and reconciliation evidence |

---

### WS-5 · QC / Validation  
**Function:** Challenge production · **Gate:** G06

| Field | Content |
|---|---|
| **Owned artifacts** | Risk-based validation plan · config/validation_strategy.yaml · recon (dataset/results/forest/admiral) · log cleanliness · findings register · disposition board · CORE local rules |
| **Current status** | **GREEN residual-risk framework; RED current qualification** — known differences and Community evidence remain filed, while current-run qualification and release verification fail closed |
| **Open risks** | Single-author tracks; log coverage = persisted logs only; Community findings open; licensed Enterprise and qualified disposition approval external |
| **Required evidence pack** | (1) Validation strategy control report · (2) Recon/admiral status · (3) Log cleanliness · (4) Findings + disposition · (5) **`docs/workstreams/WS5_KNOWN_DIFFERENCES_MEMO.md`** |
| **Release gate** | G06 |
| **Next action** | Hold residual memo current when any ACCEPTED finding changes; co-own CORE residual matrix with WS-1 |

---

### WS-6 · Regulatory Writing / Reviewer Explanation  
**Function:** Explain the package · **Gates:** G07 (primary), G08 narrative

| Field | Content |
|---|---|
| **Owned artifacts** | ADRG · SDRG · BDRG · TRACEABILITY_MATRIX · SDSP · ANALYSIS_REPORT · release note · limitation language · demo boundary |
| **Current status** | **GREEN for the controlled narrative when G07 and package freshness pass** — S1–S4 reviewer-guide hardening complete and G07 is executable |
| **Open risks** | Package PDF copies must be regenerated and visually checked whenever controlled Markdown changes; over-claim if a stale PDF is cited |
| **Required evidence pack** | (1) ADRG/SDRG/BDRG revision IDs · (2) Traceability matrix catalog-aligned · (3) is/is-not · (4) S1–S4 review notes/addenda |
| **Release gate** | G07 narrative and package freshness must pass for the current candidate |
| **Next action** | Maintain guides on claim drift; regenerate package PDFs on every controlled source change; hand residual matrix to WS-1 |

---

### WS-7 · Release Engineering / Platform  
**Function:** Prove the run · **Gates:** G08 (build), G09

| Field | Content |
|---|---|
| **Owned artifacts** | cibuild · study_manifest · renv.lock · delivery controls · evidence layers · release-run manifest · RC checklist · eCTD package/backbone · tag · CI |
| **Current status** | **RED / NO-GO** — current telemetry is partial/simulated, the release verifier and qualification context are red, and the PR remains draft until external evidence is refreshed |
| **Open risks** | ODA handshake unavailable; stale historical claims; seal ≠ submission; EXAMPLE eCTD; CI does not re-run ODA (by design) |
| **Required evidence pack** | (1) pipeline_health · (2) release_run_manifest · (3) RC status · (4) tag · (5) release note · (6) CI `path-a-seal-verify` · (7) `scripts/verify_release.py` |
| **Release gate** | G09 — PASS only for a clean, current, fully verified candidate |
| **Next action** | Reconcile live summaries to RED, keep the PR draft, retry ODA, then follow `docs/runbooks/RELEASE_PROMOTION.md` without bypassing a gate |

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
WS-7 Release ──G08/G09──► unreleased candidate (tag only after the conditional release rule passes)
```

**Rule:** If you cannot name the upstream pack you consumed, you are not operating the model.

---

## 5. Priority queue (serious order — not “more automation for fun”)

| Priority | Workstream | Deliverable | Why |
|---:|---|---|---|
| **Done** | WS-0 | `docs/PRODUCT_CLAIM.md` | Stops claim drift; career protection |
| **Done** | WS-5 | Known-differences / residual risk memo for reviewers | Makes ACCEPTED findings usable in interview/review |
| **Done** | WS-6 | ADRG/SDRG/BDRG hardening against board + claim | Reviewer package is the human product |
| **Done** | WS-1 + WS-3 | External validation evidence index (CORE residual + P21 slot + XSD + eCTD validate) | Industry-grade package layer |
| **Done** | WS-2 | Section 2 populations/endpoints audit + Phase 2 closure | Confirms live denominators, ITT TTUMOR, corrected T-11-3–T-11-8 mapping and F-042 lineage evidence |
| **Done** | WS-7 | `verify_release` + CI `path-a-seal-verify` | Operational polish without reopening science |
| **P3** | WS-4 | Deferred TFL backlog only if claim expands | Do not explode scope on GREEN programming |

---

## 6. Review cadence (how we run this like departments)

1. **Weekly workstream review (one WS per session):** walk owned artifacts → status → risks → next action only.  
2. **No review without a pack list** (files + statuses).  
3. **G09 re-seal** only when a workstream changes promotion-class evidence (not for doc typos alone).  
4. **Tag policy:** historical tags remain frozen; `v0.3.0-clinical-simulation` is a candidate identifier, not a tag, until its conditional release rule passes.

---

## 7. What success looks like at the next milestone

Not “another GREEN JSON.”

**v0.3 controlled-simulation candidate acceptance:**

- Every WS row is GREEN or WAIVED for the current run, with its pack on disk
- Known-differences memo complete  
- External validation index complete (RUN / NOT_AVAILABLE / residual)  
- ADRG/SDRG/BDRG read as controlled guides  
- `verify_release.sh` reproduces machine grades in one command  
- Product claim still honest  

**Future filing-capable/regulated-use product (only if G00 changes):**

- Real app metadata path, aCRF, Part 11 process evidence, CbzP claim resolved or removed  

---

## 8. Immediate next operation

1. Keep the candidate PR draft and the live release surfaces RED/BLOCKED.
2. Retry the genuine SAS/ODA full DAG in the empirically governed window.
3. If it succeeds, regenerate package/seals, run clean-checkout verification, and
   complete the protected PR/default-branch/tag sequence.
4. If it fails, preserve the failure and stop; do not promote historical evidence.

See [`runbooks/RELEASE_PROMOTION.md`](runbooks/RELEASE_PROMOTION.md) for the exact
commands, no-go criteria, tag verification, and rollback behavior.
