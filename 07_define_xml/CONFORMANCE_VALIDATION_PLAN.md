# Conformance Validation Plan (CVP) — ADaM define.xml + data

**Study:** TROPIC Re-Analysis (EFC6193 / XRP6258) · **Standard:** CDISC ADaMIG v1.3, Define-XML 2.1 + ARM v1.0
**Author:** Clinical Programming · **Created:** 2026-06-14 · **Status:** ACTIVE
**Governs:** the *business-rule* conformance step that sits above the schema/referential layer
(`validate_xsd.sh`, `validate_define.py`) and the SAS↔R reconciliation. Companion to
[`P21_RUNBOOK.md`](P21_RUNBOOK.md) (turn-key commands) and ADRG §6 (execution evidence).

> **Read this first — why a *plan*, not just a tool run.** For an FDA submission, conformance is a
> *controlled deliverable*, not a button. This plan states the regulatory drivers it answers to, the
> lifecycle it sits in, the engine's exact scope (and what it is **not**), the acceptance criteria,
> and the per-finding disposition path. A green report with no plan is not submission evidence.

---

## 1. Regulatory drivers (the "standard procedures")

Standardized study data is **mandatory**, not optional, for NDA/BLA/ANDA/commercial IND under
**FD&C Act §745A(a)**; the operational expectations are layered:

| # | Authority | What it requires of *this* step |
|---|---|---|
| 1 | **FDA Data Standards Catalog** | The ADaM/SDTM/CT/Define-XML **versions** used must be FDA-*supported* for the study's start date. Conformance is judged against the Catalog-pinned versions, not "latest". |
| 2 | **FDA Study Data Technical Conformance Guide (sdTCG) v6.0, Mar 2025** | §8 — conformance to standards, **data validation rules**, **traceability** (analysis → ADaM → SDTM → CRF), legacy-conversion handling. ADRG does **not** remove the need for a complete `define.xml`. |
| 3 | **FDA Technical Rejection Criteria (TRC)** — eCTD validations **1734 / 1735 / 1736** (enforced since **Sep 2021**; auto-**reject** at the Gateway, run sequentially after 1789) | **1734:** a `ts.xpt` with **Study Start Date** present. **1735:** correct STF file-tags on every standardized dataset + its define. **1736:** for ADaM, an **ADSL + define.xml** must be present. These are *submission-blocking* before a reviewer ever opens the data. |
| 4 | **Define-XML 2.1 + ARM v1.0** | The metadata roadmap. 2.1 lets each dataset cite its **ADaMIG version**; **ARM** (analysis-results metadata) is reviewer-valued and recommended (not strictly required). |
| 5 | **eCTD Module 5 + ADRG/SDRG** | Reviewer-facing context: derivations, deviations, dispositions. Findings dispositioned here must be traceable into the ADRG. |
| 6 | **21 CFR Part 11 / ALCOA+** | The validation record itself (who/what/when, audit trail, reproducibility) must be attributable, legible, contemporaneous, original, accurate + complete. |

## 2. Validation lifecycle this step lives in

```
Requirements/SAP ─▶ ADaM spec (define.xml) ─▶ Independent double programming (SAS ‖ R)
        │                                              │
        └────────────────────── QC / reconciliation (diffdf, zero-diff) ──────────┐
                                                                                   ▼
   Conformance validation (THIS PLAN)  ─▶  Finding triage + disposition  ─▶  ADRG ─▶ sign-off
```

Already satisfied upstream (verified, this branch): independent SAS↔R double programming with
**zero-diff `diffdf` reconciliation on real ODA SAS output** (7/7 domains); clean SAS + R logs;
`define.xml` **XSD-valid** + **referential-integrity PASS (273 checks)**; `renv` env pin; `logrx`
audit logs; CHANGELOG version history. **Open independence caveat:** producer and validator are not
organizationally independent (single author) — disclosed in ADRG §6; in a funded program this step
is performed by an independent validation programmer.

## 3. The engine reality — CORE vs the FDA's actual validator (do not overclaim)

This is the single most important honesty point for an FDA framing:

| Engine | Rule set | Authority | Role here |
|---|---|---|---|
| **Pinnacle 21 *Enterprise*** + **FDA Validator Rules** | FDA-published rules | **What FDA actually runs** on receipt | The authoritative pre-submission run (license + Catalog-matched FDA rule pack). |
| **Pinnacle 21 *Community*** | FDA **and** CDISC rule packs | Free desktop | Closest free analogue to the FDA run; GUI-oriented. |
| **CDISC CORE** (`cdisc-rules-engine`, open-source) | **CDISC Conformance Rules** | CDISC | **Our scriptable, reproducible CI gate.** Overlaps heavily with — but is **not identical to** — the FDA rule pack. |

**Decision for this repo:** use **CDISC CORE** as the in-pipeline, version-controlled conformance
gate (reproducible, no license, diff-able JSON output). **Stated limitation:** a CORE pass is
evidence of **CDISC** conformance and is a strong proxy, but it is **not** a substitute for the
authoritative **Pinnacle 21 + FDA Validator Rules** run matched to the Data Standards Catalog. The
submission record must carry the latter; CORE keeps the engineering track continuously clean between
those runs.

> **⚠️ Empirical finding (2026-06-14, verified against CORE v0.16.0 `rules.pkl`).** CORE currently
> ships executable rules for **SDTMIG / SENDIG / TIG / USDM only — and ZERO for ADaM/ADaMIG**. The
> ADaM Conformance Rules exist as a *specification* (CDISC v5.0, 1000+ rules, ADaMIG 1.3) but their
> executable form is **not yet released in CORE** (CORE 1.0 full delivery is on the 2026 roadmap).
> **Consequence:** for the **ADaM** layer, CORE cannot gate anything today — **Pinnacle 21**
> (mature, executable ADaM rule pack) is the **required**, not optional, engine. CORE stays our gate
> for the **SDTM** layer. Evidence + disposition: [`../06_telemetry/p21_conformance_runrecord.md`](../06_telemetry/p21_conformance_runrecord.md).

> **Interim executable gate (in-repo).** Because CORE lacks ADaM rules and P21 Community 4.1.0 is
> engine-expired under this environment's clock ([`../06_telemetry/p21_adam_runrecord.md`](../06_telemetry/p21_adam_runrecord.md)),
> a focused **ADaMIG v1.3-aligned conformance check** runs in-environment:
> `bash 06_telemetry/run_adam_conformance.sh` → `06_telemetry/adam_conformance_report.{md,csv}`.
> It implements the high-value rule families (dataset↔define.xml consistency, ADaMIG structural,
> identifier/key integrity, controlled terminology) — **not** the full FDA Validator pack and **not**
> a substitute for the authoritative P21 Enterprise run, but a real, reproducible gate that surfaces
> actual findings instead of leaving the ADaM layer unchecked.

## 4. Standards & versions under test

- ADaM: **ADaMIG v1.3** (define declares `STD.ADaMIG.1.3`); Define-XML **2.1** + ARM **1.0**.
- Datasets under test: the 7 real-MP `04_adam/*_prod.xpt` (independent SAS output, this run).
- **Controlled Terminology: GAP — `define.xml` does not declare a dated CDISC ADaM CT package.**
  CORE/P21 need a CT package to evaluate value-level (codelist) rules. **Action:** pin the
  Catalog-appropriate CDISC ADaM CT version, declare it in `define.xml`, and pass it to the engine.

## 5. Severity taxonomy & acceptance criteria

| Severity (P21/FDA) | Meaning | Disposition rule |
|---|---|---|
| **Reject** | Submission-blocking (incl. TRC 1734/35/36) | **Must fix.** Zero tolerance. |
| **Error** | Rule violation | Fix, **or** justify with a documented, reviewer-defensible rationale in the ADRG. |
| **Warning** | Likely issue | Triage each; document disposition (fix or justify) in the ADRG. |
| **Notice / Info** | FYI | Review; record if material. |

**Acceptance gate:** 0 Reject · 0 unexplained Error · every Warning dispositioned. The CORE-rule
equivalents (rule-id severities) are triaged the same way and mapped to the above.

## 6. Pre-flight checklist (run before the engine)

- [x] **TRC 1736** — `ADSL` present (`adsl_prod.xpt`).
- [x] **TRC 1734** — `TS` with Study Start Date available in source SDTM (`ts.sas7bdat`); ensure it is
      carried into the SDTM submission package + `define_sdtm.xml`.
- [ ] **TRC 1735** — STF file-tags assigned at eCTD packaging (out of scope for the science layer;
      tracked for the packaging step).
- [ ] **CT package** declared + supplied (see §4 gap).
- [x] Schema layer green (`validate_xsd.sh` → VALID; `validate_define.py` → 273 PASS).
- [x] Data = independent SAS output, zero-diff reconciled (provenance in `pipeline_health.json`).

## 7. Execution procedure (CORE)

```bash
pip install cdisc-rules-engine            # open-source CDISC Rules Engine
core update-cache                         # rules + CT cache (CDISC Library API key may be required)
core validate \
  --standard adamig --version 1-3 \
  --define 07_define_xml/define.xml \
  --dataset-path 04_adam \
  --output 06_telemetry/p21_report --output-format JSON
```
Report → `06_telemetry/p21_report.json` (a recognised telemetry path). Environment note: the engine
requires **Python ≥3.10** (this host ships 3.9.6 → a 3.10+ interpreter is provisioned for the run).

## 8. Finding disposition & traceability

For every non-pass: record `{rule id, CDISC/FDA, severity, domain/variable, count, disposition,
rationale, ADRG/SDRG cross-ref}` in a **redacted** summary committed to `06_telemetry/` (rule-level
counts only — **no patient data**). Material dispositions are mirrored into the ADRG so a reviewer
sees them in context.

## 9. Known / expected findings (pre-documented — disclosed, not hidden)

Carried from `P21_RUNBOOK.md` §"Known items" and ADRG §5:
- Constant/placeholder baseline covariates `ALBBL=38`, `LDHBL=220` (no subject-level source) — schema
  placeholders, **not** model inputs (ADRG §5.1 / SDRG §4.1).
- ECOG performance status sourced from **VS** in the trial-era public data (SDRG §2).
- Week-precision AE/disposition dates (±3.5 d) inherent to the public source (SDRG §2); partial
  `--DTC` dates are handled to missing analysis dates (clean-log remediation, CHANGELOG 3.6.1).
- `define.xml` CT-version gap (§4) — to be closed before the authoritative P21/FDA run.
