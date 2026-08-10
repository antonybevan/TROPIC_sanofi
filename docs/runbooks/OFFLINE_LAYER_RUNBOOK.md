# Offline Capability-Layer Runbook

The 37-stage pipeline (`platform/cibuild.py`, gated by `.github/workflows/ci.yml`)
builds and validates the core ADaM/SDTM/TFL/Define/eCTD deliverables, third-engine
admiral evidence, Dataset-JSON, ARS, USDM, log cleanliness, and release-manifest binding.
A remaining **additive capability layer** runs on demand beside it: the SDTMIG-3.4 uplift,
date-precision sensitivity analysis, and the CDISC CORE conformance run.

**Wiring status.** The modern exports — `export_datasetjson.py` (stage 30),
`build_ars.py` (31), `build_usdm.py` (32) — and the eCTD sequence controls
(`build_ectd_backbone.py` stage 34, `materialize_ectd.py` stage 35) are manifest stages
gated by their own exit codes in the full pipeline. They remain documented here for
**standalone reproduction**. The SDTM uplift, date-precision sensitivity analysis, and
CDISC CORE runs stay **standalone — run on demand, not orchestrated by `cibuild.py` and
not gated in CI** — for two reasons:

1. **Data.** Most read patient-level XPT (`04_analysis_datasets/adam/*_prod.xpt`, `01_source_data/real_sdtm/`,
   the `08_submission_package/m5/` tree). This repository is **data-free** (those files are git-ignored), and CI
   has no real data, so these steps cannot execute there. CI runs only the data-free
   well-formedness gates (`validate_core_rules.py`, `validate_define.py`, the demo smoke
   test). The full engine/data runs are this local runbook.
2. **Secrets / heavyweight deps.** The CORE run needs Python 3.12, a free CDISC Library
   API key, network access, and a ~127 MB engine clone (`run_core_conformance.sh`).

This file is the single index of that layer so it does not rot or become unclear how to
regenerate. Detailed per-step records live in `08_submission_package/ectd/RUN_RECORD.md`,
`platform/conformance/CORE_*RUN_RECORD.md`, and `00_governance/REPRODUCIBILITY.md §7`.

## Prerequisites

- The CI pipeline has run and the real ADaM/SDTM data + `08_submission_package/m5/` tree are present locally
  (these are the inputs the capability layer reads).
- **R** with `renv::restore()` (haven, dplyr) — for the SDTM uplift.
- **Python 3** with `lxml`, `pyyaml`, `pyreadstat`; `pip install usdm` for USDM; Python
  **3.12** + `CDISC_LIBRARY_API_KEY` for CORE (see `00_governance/REPRODUCIBILITY.md §7`).

## Run order

Run top-to-bottom; later steps consume earlier outputs. The SDTM 3.4 uplift feeds the
repo package source at `08_submission_package/m5/` and the SDTM Dataset-JSON; backbone
precedes materialize. The eCTD sequence keeps internal `m5/...` hrefs under
`08_submission_package/ectd/0000/`, as required by the sequence layout.

| # | Script | Reads | Writes | Real data? | In pipeline? |
|---|---|---|---|---|---|
| 1 | `platform/uplift_sdtm_34.R` | `01_source_data/real_sdtm/*.sas7bdat` (3.1.1, pristine) | `.core_run/sdtm34/*.xpt` + `08_submission_package/m5/.../sdtm/datasets/*.xpt` (3.4) | yes | offline |
| 2 | `03_metadata/define/uplift_define_34.py` | `03_metadata/define/define_sdtm.xml` (+ embedded 3.4 column metadata) | `03_metadata/define/define_sdtm.xml` (SDTMIG 3.4, CT 2026-03-27) | no (metadata-only) | offline |
| 3 | `platform/export_datasetjson.py` | `04_analysis_datasets/adam/*_prod.xpt`, SDTM `*.xpt` | `04_analysis_datasets/datasetjson/**/*.json` (Dataset-JSON v1.1) | yes | **stage 27** |
| 4 | `platform/build_ars.py` | MP-arm KM results | `05_outputs/ars/` (ARS v1.0 ReportingEvent + ARD) | yes | **stage 28** |
| 5 | `platform/build_usdm.py` | study metadata / `config/study_config.yaml` | `03_metadata/usdm/` (USDM v3.0 study definition) | no (study-def only) | **stage 29 + CI** |
| 6 | `platform/build_ectd_backbone.py` | `08_submission_package/m5/` tree | `08_submission_package/ectd/0000/` backbone + STF + `index-md5.txt` | yes (checksums package leaves) | **stage 31** |
| 7 | `platform/materialize_ectd.py` | `08_submission_package/ectd/0000/` backbone + `08_submission_package/m5/` | content copied into `08_submission_package/ectd/0000/`, MD5 re-verified | yes | **stage 32** |
| 8 | `platform/date_precision_sensitivity.py` | real MP-arm time-to-event data | `platform/conformance/date_precision_sensitivity.json` | yes | offline |
| 9 | `platform/run_core_conformance.sh` | uplifted 3.4 SDTM, 3.1.1 source, `*_prod.xpt`, defines | `platform/conformance/core_{sdtm34,sdtm,adam}_report.json` | yes + network + API key | offline |

```bash
# data layer (1–2)
Rscript platform/uplift_sdtm_34.R
python3 03_metadata/define/uplift_define_34.py
# modern machine-readable exports (3–5)
python3 platform/export_datasetjson.py
python3 platform/build_ars.py
python3 platform/build_usdm.py
# eCTD sequence (6–7)
python3 platform/build_ectd_backbone.py
python3 platform/materialize_ectd.py
# sensitivity + conformance (8–9)
python3 platform/date_precision_sensitivity.py
export CDISC_LIBRARY_API_KEY=<free CDISC account key>
bash platform/run_core_conformance.sh
```

## Determinism / what is committed

Each step is deterministic for fixed inputs and **additive** — none modifies the pristine
source or the CI-built deliverables. Committed artifacts are the data-free outputs and the
run records (backbone XML, STF, define, run records); patient-level outputs (XPT,
Dataset-JSON, CORE reports, materialized payload) are git-ignored and regenerated by the
steps above.
