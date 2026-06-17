# Executable CDISC CORE Conformance Rules (ADaM)

This directory holds **executable ADaM conformance rules in CDISC CORE format** (YAML),
runnable in the official [CDISC Open Rules Engine (CORE)](https://www.cdisc.org/core).

## Why this exists

As of **2026-06**, CDISC/CORE publishes executable conformance rules for **SDTMIG, SENDIG,
TIG, and USDM — but the ADaM (`adamig`) rule pack is empty** (verified: `adamig/1-0..1-3`
contain **0 rules**; `core update-cache` fetched zero ADaM rules from the CDISC Library).
This is consistent with the project's ADRG §6 statement. The mature ADaM validator is
Pinnacle 21 (desktop, not pipeline-scriptable).

To get **executable, scriptable, CI-able ADaM conformance** anyway, we author the rules
ourselves in CORE's YAML format and run them via CORE's `--local-rules` mechanism. Each rule
is traceable (Authorities → CDISC ADaMIG / ADaM Conformance Rules) and runs in the real CDISC
engine — not a bespoke checker.

> **Scope honesty:** this is a *seed* pack (required-key-variable population across all 7 ADaM
> datasets), not the full official 1000+-rule ADaM Conformance Rules v4.0/v5.0 set. The IDs are
> `TROPIC-ADAM-###` placeholders pending a 1:1 mapping to official `AD####` IDs (the official
> rules spreadsheet requires a CDISC account to download). The pattern is the transferable asset.

## Rules

| File | Dataset | Check |
|---|---|---|
| `TROPIC-ADAM-101` | ADSL | `USUBJID` populated |
| `TROPIC-ADAM-102` | ADAE | `USUBJID` populated |
| `TROPIC-ADAM-103` | ADCM | `USUBJID` populated |
| `TROPIC-ADAM-104` | ADTTE | `PARAMCD` populated |
| `TROPIC-ADAM-105` | ADLB | `PARAMCD` populated |
| `TROPIC-ADAM-106` | ADRS | `PARAMCD` populated |
| `TROPIC-ADAM-107` | ADEX | `PARAMCD` populated |

Latest run (CORE 0.16.0): **7/7 SUCCESS, 0 issues** — see `../conformance/core_adam_report.json`
and `../conformance/CORE_RUN_RECORD.md`.

## Running

See `../run_core_conformance.sh` for full reproducible setup. In short:
```bash
core validate -s adamig -v 1.3 -d <adam_xpt_dir> -ft xpt \
  -lr 06_telemetry/conformance_rules/adam -ca <cache> -ps 1 -of JSON -o <out>
```

## Known engine caveats (CORE 0.16.0)

- **One rule per (dataset, operator) per invocation.** Two same-operator rules targeting the
  *same* dataset collide in CORE's operation-result cache (the second reports an execution
  error). This pack is structured one-rule-per-dataset to avoid it. (Each rule also validates
  cleanly in isolation.)
- **CLI gate bug:** CORE's `StandardTypes` gate rejects `-s adamig` even though the engine's
  `normalize_adam_input()` requires it. The runner applies a one-line local patch
  (`enums/standard_types.py`) to add `adamig`; reported for upstream.
- **Define-XML (RESOLVED):** both defines now parse in CORE (`Define_XML_Version 2.1.0`). Three
  defects were fixed — invalid `Role` on `ItemGroupDef`, empty `TranslatedText`, and the missing
  `def:Class` element (the root cause of `'NoneType'.Name`) — added to all SDTM + ADaM datasets.
  The ADaM rules run with the define engaged; both defines still pass the project's XSD.

## CI

`06_telemetry/validate_core_rules.py` checks every rule here is well-formed and has the required
CORE keys (no CDISC API key or data needed) — wired into `.github/workflows/ci.yml`. A full
conformance run (which needs `CDISC_LIBRARY_API_KEY` for library metadata) is the documented
local/secret-gated step in the runner.
