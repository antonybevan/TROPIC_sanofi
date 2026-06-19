# I/J Platform Generalisation — Implementation Plan (P0–P2)

> Source: 2026-06 strategic validation analysis, Findings I + J ("generalise the
> orchestration + reconciliation engine to a study-agnostic, config-driven
> multi-study platform"). Scope chosen: **P0–P2** (manifest-drive in-repo + prove
> with a stub second study). Physical-layout variant: **pragmatic** (TROPIC stays
> at repo root as the default study; a second study lives under `studies/`).

## End-state

A **study manifest** (`study_manifest.yaml`) declares pipeline *structure* the way
`study_config.yaml` already declares clinical *parameters*. The existing engine
(`cibuild.py`, `cross_lang_audit.R`, `results_reconcile.R`) reads structure from the
manifest instead of hardcoding it. A second stub study (`DEMO02`, ADSL + ADAE only)
runs end-to-end through the *same* engine — the proof of study-agnosticism.

## Why a declarative manifest (not filename auto-discovery)

Program names are *almost* mechanical (`A_<ds>_generation.sas` /
`v_<ds>_validation.R`) but carry exceptions that cannot be derived:

| Exception | Detail |
|---|---|
| ADAE | `A_adae_io_respec.sas` / `v_adae_io_validation.R` (not `A_adae_generation.sas`) |
| BIMO → clinsite | validated by `v_bimo_validation.R`, but the **dataset is named `clinsite`** |

A declarative manifest captures these explicitly; auto-discovery would silently
mis-wire them.

## Coupling inventory (the work surface)

| # | Coupling | Location |
|---|---|---|
| 1 | 17-stage DAG as a literal Python list | `cibuild.py:492–514` |
| 2 | Dataset list hardcoded 5× | `cibuild.py:114`, `cibuild.py:330`, `cross_lang_audit.R:150`, `_oda_render_tfl.py:40`, validation stages |
| 3 | Per-dataset business keys (if/else) | `cross_lang_audit.R:62–78` |
| 4 | Study identity strings | `cibuild.py:458/709/754`, `cross_lang_audit.R:178/183`, `00_master_driver.sas:7` |
| 5 | Study-specific SAS results-recon embedded | `cibuild.py:253–272` (`adtte`, `TRT01P='MP'`) |
| 6 | R results-recon arm/dataset hardcoded | `results_reconcile.R:55–57` |
| 7 | Hand-rolled flat YAML parser (no nesting) | `generate_config.py:4–33` |

Assets to build on (do not rebuild): name-keyed gate assertions
(`cibuild.py:519–529`), env-var de-hardcoding ("roadmap #10"), per-dataset CORE
rule YAMLs, and `compare_datasets()` already taking `ds_name` as a parameter.

## Decisions taken

- **YAML library:** use `pyyaml` for the new nested `manifest.py`. It is already a
  CI dependency (`.github/workflows/ci.yml` installs it) and the R side already
  uses `yaml`. `generate_config.py`'s flat parser is **left untouched** (surgical).
  CI is hardened by promoting `pyyaml` to the main Python-deps step.
- **Physical layout:** pragmatic — TROPIC stays at repo root (default study); a
  `--study <name>` flag resolves a manifest/config/program root under `studies/`.
  No-flag invocation behaves exactly as today. Full `engine/` extraction is P3.
- **Defensive fallback:** if the manifest is missing/unreadable, the engine falls
  back to the legacy hardcoded dataset list + identity, so no regression is possible.

## The manifest (`study_manifest.yaml`)

```yaml
study:    { id, code, title }
datasets: [ { name, keys, val, sas, order|parallel_group, results_recon? } ]
infrastructure_stages:
  pre:  [ ingest, sdtm-validation ]
  post: [ cross-lang-recon (gated), tfl (gated), results-recon (gated),
          define-conformance, data-conformance, ectd-package ]
```

## Phases

### Phase 0 — De-duplicate to one source *(low; pure refactor, zero behaviour change)*
1. New `study_manifest.yaml` (root).
2. New `06_telemetry/manifest.py` — pyyaml loader + helpers
   (`load_manifest`, `dataset_names`, `business_keys`, `study_identity`).
3. `cibuild.py`: dataset lists (`:114`, `:330`) and identity strings
   (`:458/709/754`) sourced from the manifest (with legacy fallback).
4. `cross_lang_audit.R`: dataset list (`:150`) + key-map (`:62–78`) +
   identity (`:178/183`) read from the manifest.
5. `_oda_render_tfl.py`: `DATASETS` (`:40`) sourced from the manifest.
6. CI: promote `pyyaml` to the main Python-deps step.
7. **Verify:** sim run + `--demo` + a real `cross_lang_audit.R` execution;
   reconciliation stays 8/8 PASS; identity strings intact.

### Phase 1 — Manifest-drive the DAG + reconciler *(medium)*
1. `build_stages(manifest)` assembles the ordered stage list from the manifest
   (replaces `cibuild.py:492–514`).
2. Parallel batch driven by `parallel_group` membership (replaces the
   `stages[3:8]` slice).
3. Gate-name assertion sourced from `gated: true` manifest entries.
4. Embedded SAS results-recon (`cibuild.py:253–272`) + `results_reconcile.R`
   read dataset/arm/proc from the manifest.
5. **Verify:** TROPIC stage list/order/gates byte-identical (golden file); output
   unchanged — only the *source* of structure changes.

### Phase 2 — Prove with a second study `DEMO02` *(medium-high)*
1. `studies/DEMO02/`: own `study_manifest.yaml` + `study_config.yaml`, ADSL+ADAE
   programs + validation scripts + tiny synthetic seed.
2. `cibuild.py --study DEMO02` resolves roots under `studies/DEMO02/`; no flag =
   repo root = TROPIC (back-compat).
3. Submission-tail stages (eCTD/define/CORE) optional per-study.
4. **Verify (the proof):** `cibuild.py --study DEMO02` runs green on 2 datasets
   with **zero engine edits**; TROPIC still green unchanged.
   Add `tests/test_multistudy` asserting both studies resolve + reconcile.

## Risks & mitigations
- Silent gate detachment → keep startup gate-name assertion, sourced from manifest.
- Parallel-group regression → golden-file TROPIC's generated stage list.
- Path threading bugs in P2 → default-to-root keeps TROPIC paths literally unchanged.
- Scope creep into full relocation → explicitly P3.

## Out of scope (P3+)
Physical `engine/` extraction + packaging; per-study config repos; turning DEMO02
into a full submission.
