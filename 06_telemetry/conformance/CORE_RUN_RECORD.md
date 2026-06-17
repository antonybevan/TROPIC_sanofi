# CDISC CORE Conformance Run Record

**Date:** 2026-06-17 · **Engine:** CDISC Open Rules Engine (CORE) **0.16.0** (open-source, MIT)
**Runner:** `06_telemetry/run_core_conformance.sh` · **Rules:** `06_telemetry/conformance_rules/adam/`

This records a run of the **official CDISC reference engine** against the project's data — the
real business-rule layer the home-grown `adam_conf_check.R` was a stand-in for.

---

## ADaM — executable custom rules via CORE `--local-rules`

| | |
|---|---|
| Standard | `adamig` v1.3 |
| Datasets | ADSL, ADAE, ADCM, ADTTE, ADLB, ADRS, ADEX (7 `*_prod.xpt`; `clinsite` excluded — BIMO, not ADaM) |
| Result | **7 / 7 rules SUCCESS, 0 issues** (`core_adam_report.json`) |

**Why custom rules:** CORE/CDISC Library publishes **no executable ADaM rules** as of 2026-06.
Verified directly: `adamig/1-0..1-3` rule sets are **empty (0 rules)** and `update-cache` fetched
zero ADaM rules from the Library. (SDTMIG 3.2/3.3/3.4 carry 392/423/430 rules; SENDIG/TIG/USDM
also populated.) This **confirms the ADRG §6 statement** ("CORE ships no executable ADaM rules
yet — SDTM/SEND/TIG/USDM only") rather than contradicting it. We therefore authored executable
ADaM rules in CORE YAML format and ran them through the real engine — see `../conformance_rules/`.

## SDTM — CORE's published SDTMIG rules

| | |
|---|---|
| Standard | `sdtmig` v3.2 (closest with rules; **source data is SDTMIG 3.1.1** — version gap, see below) |
| Datasets | DM, AE, EX, DS, VS (converted source `.sas7bdat` → v5 XPT) |
| Result | 392 rules executed → **110 SUCCESS, 15 ISSUE REPORTED, 265 SKIPPED (n/a to these domains), 2 engine errors**; 47 finding rows (`core_sdtm_report.json`) |

**Version-gap caveat (read before citing findings):** the public source SDTM is **SDTMIG 3.1.1**,
but CORE's lowest executable rule set is **3.2**. A large share of the 15 issue-reporting rules are
3.2-era expectations the trial-era 3.1.1 data predates (e.g. `EPOCH` required, `AEBODSYS`=`AESOC`,
`AGE`/`AGEU`), plus artifacts of the de-identified reconstruction. This is a genuine reference-engine
run that surfaces real structural items — it is **not** a clean conformance pass and must not be
presented as one.

---

## Findings this run surfaced (that the project's own checks missed)

1. **`define_sdtm.xml` defects (FIXED this session):** an invalid `Role` attribute on all 16
   `<ItemGroupDef>` elements (`Role` is valid on `ItemRef`, not `ItemGroupDef`) and 16 empty
   `<TranslatedText>` dataset descriptions — both crash CORE's `odmlib` parser. Removed `Role`
   and populated the descriptions; the define **still passes the project's XSD validation**.
2. **Deeper define loader issue (OPEN):** after the above, both `define_sdtm.xml` and `define.xml`
   still fail CORE's `odmlib` loader with `'NoneType' object has no attribute 'Name'` (an
   unresolved reference during metadata load). Define-*based* CORE rules can't run until this is
   resolved; dataset-level rules run fine without the define.
3. **CORE 0.16.0 CLI bug (patched locally, reported upstream):** the `StandardTypes` gate rejects
   `-s adamig` although the engine's `normalize_adam_input()` requires it.

## Reproducing

```bash
export CDISC_LIBRARY_API_KEY=<free CDISC account key>   # one-time, for library metadata cache
bash 06_telemetry/run_core_conformance.sh
```
The engine, venv, rule cache, and converted XPT are all under gitignored `.core_run/` / `.core_venv/`.
Only the rule pack (`conformance_rules/`), the two JSON reports, and this record are committed.
