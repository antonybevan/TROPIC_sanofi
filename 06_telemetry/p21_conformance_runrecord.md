# Conformance Run Record — CDISC CORE (ADaM)

**Date:** 2026-06-14 · **Engine:** CDISC CORE (CDISC Open Rules Engine) **v0.16.0**, standalone
mac-apple-silicon build, run **offline** against the engine's bundled rules/CT cache (no CDISC
Library API key needed).
**Raw engine output:** [`p21_report.json`](p21_report.json).

## Command
```bash
core validate -s adam -v adamig-1-3 -ca resources/cache \
  -d 06_telemetry/_p21_datasets -ft xpt \
  -o 06_telemetry/p21_report -of JSON
```
(7 real-MP ADaM `*_prod.xpt`, domain-named, from the zero-diff ODA run; CHANGELOG 3.6.1.)

## Result — and the material finding
- ✅ Engine provisioned and executed; **all 7 ADaM datasets were read and recognised** with correct
  record counts (ADSL 371, ADEX 13052, ADCM 24534, ADAE 5428, ADLB 78619, ADRS 2904, ADTTE 2058).
- ⚠️ **0 rules executed** (`Rules_Report: []`). **Root cause (verified by inspecting the engine's own
  `rules.pkl`, 981 rules): CORE v0.16.0 ships executable rules for `SDTMIG`, `SENDIG`,
  `SENDIG-DART/GENETOX/AR`, `TIG`, `USDM` — and ZERO for ADaM/ADaMIG.**

| Standard in CORE cache | Executable rules | ADaM coverage |
|---|---|---|
| SDTMIG 3.2/3.3/3.4 | ✅ ~⅔ of 336 published | — |
| SENDIG (+DART/GENETOX/AR), TIG, USDM | ✅ | — |
| **ADaMIG 1.0–1.3 / OCCDS** | ❌ **none published yet** | **engine cannot gate ADaM** |

This is **not** a defect in the datasets or a misconfiguration. The CDISC **ADaM Conformance
Rules** exist as a *specification* (v5.0, 1000+ rules, covers ADaMIG 1.3), but their **executable**
form has **not yet been released in CORE** (CORE 1.0 full delivery is on the 2026 roadmap; SDTM is
partially published, ADaM pending).

## Disposition
- A CORE ADaM run is **INCONCLUSIVE today** — there is no ADaM rule pack to run. Recorded honestly;
  the empty `p21_report.json` must **not** be read as "0 findings / conformant."
- **ADaM business-rule conformance must be run on Pinnacle 21** (Community or Enterprise), which has
  a mature, executable ADaM rule pack. This confirms Pinnacle 21 as the **required** path for ADaM
  until CORE's ADaM pack ships.
- CORE remains the right **SDTM-layer** gate (full SDTMIG pack) and is wired for that use; an SDTM
  run requires exporting the SDTM source to v5 XPT first (CORE does not read `.sas7bdat`).

## What this changes upstream
- Authoritative submission conformance still = **Pinnacle 21 + FDA Validator Rules** (FDA's own
  engine), matched to the Data Standards Catalog. CORE was the open-source proxy; for ADaM that
  proxy is **not yet available**, so P21 is load-bearing, not optional.
- Pre-flight CT-version gap still stands for the P21 ADaM run.
