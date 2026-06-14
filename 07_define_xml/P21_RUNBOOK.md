# Pinnacle 21 / CDISC CORE Conformance Runbook (business-rule layer)

**Status: DEFERRED — requires the licensed/proprietary engine + the full dataset, neither of
which can be committed to a public repo.** This runbook makes the step turn-key for anyone who
*does* have them. It is the business-rule complement to the schema-layer validation that this
repo already passes in-repo (`07_define_xml/validate_xsd.sh` → *XSD: VALID*; see ADRG §6).

## What each layer covers (and why this one is separate)

| Layer | Tool (in this repo) | What it proves | Runs on a clean clone? |
|---|---|---|---|
| XML schema | `validate_xsd.sh` (xmllint vs vendored CDISC XSD) | Structure, namespaces, required attributes, enumerations, element ordering, ARM | **Yes** |
| Referential integrity | `validate_define.py` | Every `ItemRef`/`WhereClauseRef`/`ValueListRef`/`leaf` resolves; no dangling OIDs | **Yes** |
| **Business rules** | **Pinnacle 21 / CDISC CORE (this runbook)** | metadata-vs-data consistency, value-level completeness, CT, FDA/CDISC rule packs | **No — needs data + engine** |

A green XSD/referential check is necessary but **not** sufficient for submission; the business-rule
report is the pre-submission gate and is intentionally not faked here.

## Inputs the engine needs

1. The 7 ADaM transport files `04_adam/*.xpt` (git-ignored — produced by a pipeline run; for a
   genuine SAS↔R run see `06_telemetry/ODA_GUIDE.md`).
2. `07_define_xml/define.xml` (committed).
3. The matching CDISC Controlled Terminology package for the ADaM version (ADaMIG v1.3).

## Option A — CDISC CORE (open-source, scriptable)

> **⚠️ CORE does not yet cover ADaM (verified 2026-06-14, CORE v0.16.0).** The engine's bundled
> rules ship SDTMIG / SENDIG / TIG / USDM only — **0 executable ADaM rules** (the ADaM pack is on the
> CORE 2026 roadmap). A CORE ADaM run today reads the datasets but executes **0 rules** — inconclusive,
> not a pass. **Use Option B (Pinnacle 21) for ADaM.** CORE is still valid for the **SDTM** layer
> (export SDTM to v5 XPT first — CORE does not read `.sas7bdat`). See
> [`../06_telemetry/p21_conformance_runrecord.md`](../06_telemetry/p21_conformance_runrecord.md).

```bash
# Install the open-source CDISC Rules Engine
pip install cdisc-rules-engine

# Run the ADaM rule pack against the datasets + define
core validate \
  --standard adamig --version 1-3 \
  --define 07_define_xml/define.xml \
  --dataset-path 04_adam \
  --output 06_telemetry/p21_report \
  --output-format JSON

# Result lands at 06_telemetry/p21_report.json (already a known telemetry path).
```

## Option B — Pinnacle 21 Community (GUI/CLI)

> **Run status (2026-06-14):** the full P21 Community 4.1.0 CLI toolchain was provisioned and the
> ADaM validation launched, but it is **blocked by P21's engine self-expiry** (`expirationDate
> 2025-03-31` vs the environment clock 2026-06-14; no newer Community build exists). The exact,
> ready-to-run command and the legitimate paths to complete it are in
> [`../06_telemetry/p21_adam_runrecord.md`](../06_telemetry/p21_adam_runrecord.md). For ADaM on an
> environment with a future-dated clock, **Pinnacle 21 Enterprise** (no self-expiry) is the path.

1. Open Pinnacle 21 Community → **Define.xml + Data** validation.
2. Engine = FDA or CDISC; Standard = **ADaM 1.3**; CT = matching package.
3. Data = `04_adam/`; Define = `07_define_xml/define.xml`.
4. Export the report to `06_telemetry/p21_report.xlsx` (and JSON if scripting via the P21 CLI).

## Acceptance / how to read the result

- Triage every **Reject** and **Error**; document each **Warning** with a justification in the ADRG.
- Commit a redacted summary (rule id, severity, count, disposition) — not patient data — as the
  conformance evidence. `06_telemetry/p21_report.json` is a recognised telemetry artifact.

## Known items this repo already expects the report to flag (documented, not hidden)

- Constant/placeholder baseline covariates `ALBBL=38`, `LDHBL=220` (no subject-level source) —
  carried as schema placeholders, **not** model inputs (ADRG §5.1 / SDRG §4.1).
- ECOG performance status sourced from the **VS** domain in the trial-era PDS data (SDRG §2).
- Week-precision AE/disposition dates (±3.5 days) inherent to the public source (SDRG §2).
