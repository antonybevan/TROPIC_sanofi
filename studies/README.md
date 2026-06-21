# Studies — multi-study engine (I/J platform generalisation)

The TROPIC pipeline engine (`06_telemetry/cibuild.py` + `06_telemetry/manifest.py` +
the shared reconciler `05_reconciliation/cross_lang_audit.R`) is **study-agnostic**:
the pipeline *structure* lives in a per-study `study_manifest.yaml` and the clinical
*parameters* in a per-study `study_config.yaml`, not in engine code.

- **Default study** = TROPIC, at the repo root (`./study_manifest.yaml`). Run it the
  usual way: `python3 06_telemetry/cibuild.py [--real-sas | --use-cached-sas | ...]`.
- **A named study** lives under `studies/<name>/` and runs through the *same* engine:

  ```bash
  python3 06_telemetry/cibuild.py --study <name>
  ```

  The engine `chdir`s into `studies/<name>/`, builds the DAG from that study's
  manifest, and resolves shared engine scripts (manifest entries flagged
  `engine: true`) back to the repo-root engine.

## Adding a study

Create `studies/<name>/` with:

| Path | Purpose |
|---|---|
| `study_manifest.yaml` | Pipeline **structure**: `study` identity, `datasets` (name, business `keys`, `val` script, optional `parallel_group`/`order`/`val_stage`/`results_recon`), and `infrastructure_stages` (`pre`/`post`, each with a `runner` of `logrx`/`rscript`/`python`, plus `engine: true` for shared engine scripts and `gated: true` where a QC gate applies). |
| `study_config.yaml` | Clinical **parameters** (consumed by `generate_config.py` → `02_production_sas/00_config_generated.sas`). |
| `03_validation_r/*.R` | The validation-track programs named by each dataset's `val:`. They write `04_adam/<name>_v.xpt`. |
| `02_production_sas/` | SAS production programs (optional; an R-only sim study may leave this empty). |

The engine writes that study's outputs (`04_adam/`, `06_telemetry/`) under its own
root, so studies never collide.

## `DEMO02`

`DEMO02/` is a deliberately tiny proof study — ADSL + ADAE, fully synthetic, no SAS —
that exercises ingest-free validation → SAS-sim byte-copy → cross-language
reconciliation through the unchanged engine. It is the concrete demonstration that the
platform runs more than one study.
