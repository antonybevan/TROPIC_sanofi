# 10_datasetjson — CDISC Dataset-JSON v1.1 transport layer

Modern, regulator-aligned exchange format for the TROPIC analysis and tabulation
data, generated **in addition to** the existing SAS Transport v5 (`*.xpt`). This
folder is produced, never hand-edited.

## Why

FDA and PMDA are transitioning the dataset exchange format from SAS Transport v5
(XPT — 8-char variable names, 40-char labels, 200-char text ceiling) to
**CDISC Dataset-JSON v1.1**. The pipeline previously emitted XPT only
(`02_production_sas/U_xpt_export.sas`). This layer closes that gap without touching
the validated XPT path.

## Contents

| Path | Source | Standard metadata |
|---|---|---|
| `adam/<name>.json` | `04_adam/<name>_prod.xpt` (8 datasets) | `MDV…ADAM.1.3`, `define.xml` |
| `sdtm/<name>.json` | `m5/…/tabulations/sdtm/datasets/<name>.xpt` (34 datasets) | `MDV…SDTM.3.1.1`, `define_sdtm.xml` |

## How it is built

```bash
python3 06_telemetry/export_datasetjson.py          # ADaM + SDTM
python3 06_telemetry/export_datasetjson.py --adam   # ADaM only
python3 06_telemetry/export_datasetjson.py --sdtm   # SDTM only
```

`export_datasetjson.py`:

- reads each XPT with `pyreadstat` (datetime conversion disabled, so SAS date/time
  variables keep their exact stored numeric and carry the SAS format in
  `displayFormat` — lossless and XPT-round-trippable);
- emits `itemOID`/`itemGroupOID`/`studyOID`/`metaDataVersionOID` consistent with the
  project Define-XML, and `keySequence` from the business keys in
  `study_manifest.yaml`;
- **validates every file in-process against the CDISC Dataset-JSON schema the
  project's CORE engine enforces**
  (`.core_run/engine/resources/schema/dataset.schema.json`, JSON-Schema draft
  2019-09).

## Conformance / QC status

- 42 / 42 datasets schema-**VALID** (Dataset-JSON v1.1.0).
- Round-trip verified lossless: every file re-read the way CORE's
  `DatasetJSONReader` reads it, reconciled cell-for-cell against the source XPT
  (0 mismatches; ADLB checked at 2,122,713 cells). No `NaN`/`Infinity` tokens.

## Scope notes

- Values are preserved exactly as stored in XPT; this is a **format** modernization,
  not a content change. It does not alter the underlying SDTMIG/ADaMIG versions —
  see `06_telemetry/SUBMISSION_STANDARDS_REMEDIATION.md`.
- These files are data-bearing and are excluded from the data-free `m5` preview by
  the same `.gitignore` policy that excludes `*.xpt` (add a matching rule if needed).
