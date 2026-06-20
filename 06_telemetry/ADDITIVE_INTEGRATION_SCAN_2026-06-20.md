# Additive-Integration Scan — emerging standards TROPIC is still missing (2026-06-20)

A literature/standards grind against the current CDISC + FDA roadmap to find layers the
package could add **additively** (the way Dataset-JSON v1.1 and the eCTD STF already
were), without touching the validated SAS↔R pipeline, defines, or XPT.

**Scan basis (researched, dated):** FDA Study Data Technical Conformance Guide **v6.0
(March 2025)**; FDA **Dataset-JSON v1.1** Federal-Register notice (**April 2025**) +
PHUSE/CDISC pilot; CDISC **Analysis Results Standard (ARS) v1.0** (adoption from **May
2025**, catalog versions targeted **2027**); CDISC **Digital Data Flow / USDM** (DDF-RA,
USDM v3 final, **v4.0 in public review**, white paper **Dec 2025**); CDISC **360i**
(Feb 2025: USDM, Biomedical Concepts, Dataset Specializations, Data Contracts).

**Verified absent in the repo** (grep, excluding vendored engine): no
`analysis-results-standard` / `ReportingEvent` (ARS), no `Digital Data Flow` / USDM
study definition, no `SDSP`, no `biomedical concept`, no `dataset specialization`. The
package *does* have ARM v1.0 in `define.xml` — the natural seed for ARS.

---

## Tier 1 — high value, additive, buildable in this environment

### A. CDISC Analysis Results Standard (ARS) v1.0 + Analysis Results Datasets (ARD)
- **What:** machine-readable analysis results metadata — a `ReportingEvent` →
  `Analysis` → `Method`/`Operation` → `Output` graph — plus the **ARD**, the structured
  dataset holding the actual result values. The successor to define-level ARM.
- **Why now:** ARS v1.0 is released; CDISC encourages adoption from May 2025 as the
  end-to-end-traceability capstone of 360i.
- **TROPIC today:** has ARM v1.0 (8 ResultDisplays / 10 AnalysisResults in `define.xml`)
  and the numeric results already live in `09_tfl/output/tables/*` — but **no ARS
  instance and no ARD.** The hard part (results + method linkage) already exists.
- **Build here:** generate an ARS `ReportingEvent` JSON from the ARM + TFL results, and
  emit the ARD (one tidy results table: analysis-id, method, operation, group, value).
  Pure JSON/CSV generation; validates against the ARS LinkML schema. **Recommended #1.**

### B. USDM / Digital Data Flow machine-readable study definition
- **What:** a `usdm`-conformant JSON `Study` (identifiers, phase, arms, objectives &
  endpoints, eligibility, interventions, schedule) — the machine-readable protocol.
- **Why now:** DDF/USDM is the front end of CDISC 360i; FDA is engaged; USDM v4.0 is in
  review. CORE already ships executable USDM rules (so it's checkable).
- **TROPIC today:** has a protocol PDF, SAP `.docx`, and `study_config.yaml`/
  `study_manifest.yaml` — structured inputs — but **no USDM instance.**
- **Build here:** assemble a USDM v3 `Study` JSON from `study_config.yaml` + protocol
  facts; validate with the `usdm` Python package / CORE. Feasible additively.

---

## Tier 2 — valuable, light, buildable here

### C. Study Data Standardization Plan (SDSP)
- FDA sdTCG v6.0 recommends an SDSP describing the standards, versions, and any
  exceptions used. TROPIC has the *content* scattered across the reviewer guides but no
  consolidated SDSP. **Build here:** one additive markdown/PDF assembled from the
  existing standards declarations. Easy; reviewer-friendly.

### D. Dataset-JSON **NDJSON** variant
- The FDA pilot and the CORE engine support newline-delimited Dataset-JSON (streaming-
  friendly for large datasets like ADLB/LB). **Build here:** a `--ndjson` switch on the
  existing `export_datasetjson.py`. Small, completes the transport-modernization story.

---

## Tier 3 — emerging, but needs CDISC Library / heavier (lean terminal)

### E. Biomedical Concepts + SDTM Dataset Specializations
- The 360i metadata layer (value-level definitions driving metadata automation). BCs are
  now exposed as JSON via the CDISC Library API. **Needs** a CDISC Library API key and a
  modeling pass — better suited to the terminal session.

### F. eCTD v4.0 (ICH RPS)
- I generated a v3.2.2 backbone (`11_ectd/0000/`). v4.0/RPS is the forward target but is
  region-gated and heavier; defer until a gateway target is chosen.

---

## Recommendation

Build **A (ARS v1.0 + ARD)** next: it is the highest-traceability payoff, sits directly
on top of the ARM and TFL results the package already has, and is fully additive and
verifiable here. **B (USDM)** is the strong second — it adds a machine-readable study
definition the package completely lacks and is CORE-checkable. C and D are quick wins; E
and F are terminal/forward-looking.

| # | Integration | Value | Feasible here | Status |
|---|---|---|---|---|
| A | ARS v1.0 + ARD | High | Yes | **BUILT** — `12_ars/` (validation PASS) |
| B | USDM / DDF study def | High | Yes | **BUILT** — `13_usdm/` (usdm_model-validated) |
| C | SDSP document | Med | Yes | **BUILT** — `08_reviewers_guides/SDSP.md` |
| D | Dataset-JSON NDJSON | Med | Yes | **BUILT** — `10_datasetjson/**/*.ndjson` (lossless) |
| E | Biomedical Concepts / Dataset Specializations | Med | Partial (needs Library) | terminal |
| F | eCTD v4.0 (RPS) | Med | Partial | defer |

**Build log (2026-06-20).** A–D built additively and verified:
ARS ReportingEvent + ARD (4 analyses, referential-integrity PASS; results = verified
MP-arm KM); USDM v3.0.0 Wrapper (68 entities, constructed through the official
`usdm_model` Pydantic classes); SDSP consolidating standards/exceptions; Dataset-NDJSON
for all 42 datasets (round-trip lossless). Generators: `06_telemetry/build_ars.py`,
`build_usdm.py`, and the `--ndjson` flag on `export_datasetjson.py`. E and F remain
terminal/deferred.

*Sources: cdisc.org/standards/foundational/analysis-results-standard; cdisc.org/ddf;
github.com/cdisc-org/{analysis-results-standard,usdm,DDF-RA}; FDA sdTCG v6.0 (March
2025); FDA Dataset-JSON Federal-Register notice (April 2025); CDISC 360i.*
