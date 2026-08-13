# Repository Surface Policy

**Purpose:** Track the controlled review surface, source spine, and minimum durable evidence.

**Product claim:** controlled clinical-submission simulation (`docs/PRODUCT_CLAIM.md`).
**Audience:** Interviewers, reviewers, future self.

This is **not** “put every run artifact on GitHub.”  
This is **reproducible factory + honest sealed evidence + clean review face.**

---

## 1. What interviewers are meant to see

| Order | Open | Why |
|---:|---|---|
| 1 | Root `README.md` | Claim + dual surface |
| 2 | `docs/PRODUCT_CLAIM.md` | What we may assert |
| 3 | `08_submission_package/m5/` | Module 5–style **review package** (data-free preview) |
| 4 | `07_reviewer_explanation/guides/` | ADRG · cSDRG source · BDRG |
| 5 | `docs/RELEASE_NOTE_v0.3.0-clinical-simulation.md` | Current controlled release narrative |
| 6 | `python3 scripts/verify_release.py` | Re-check seals without SAS |
| 7 | `docs/SCRIPT_MAP.md` · `platform/README.md` | If they want the factory |

**Interview line:**  
Package under `m5/`. Factory is programs, orchestration, and evidence. Patient data are not in Git. CbzP is synthetic/reconstructed and TFL-only. This is not a filing.

Full walk: [`INTERVIEWER_GUIDE.md`](INTERVIEWER_GUIDE.md).

---

## 2. What stays in git (TRACK)

### A. Review surface (product face)

- `08_submission_package/m5/` structure: define, programs, TFLs (png/txt), guide PDFs, CSR  
- **No** patient-level `*.xpt` / `*.sas7bdat` in git  
- eCTD backbone shell under `08_submission_package/ectd/0000/` (index/STF/DTD; not full data payload)

### B. Source of truth (factory spine)

- `04_analysis_datasets/programs/{sas,r}/` — dual-language ADaM  
- `05_outputs/tfl/*.R` — TFL programs  
- `06_qc_evidence/reconciliation/*.R` — recon programs  
- `02_specifications/sap/` — SAP authority  
- `03_metadata/` — ADaM spec, define sources, schemas (not patient data)  
- `config/*.yaml` — manifest, catalog, controls  
- `platform/*.py` / core runners — orchestrator, packager, gates  
- `scripts/verify_release.py`  
- `tests/` · `renv.lock` · `00_governance/REPRODUCIBILITY.md`

### C. Controlled narrative (human docs)

- `docs/PRODUCT_CLAIM.md`  
- `docs/RELEASE_NOTE_*.md` · human seal summaries  
- `docs/SCRIPT_MAP.md` · `docs/INDEX.md` · this policy  
- `docs/workstreams/` packs that explain residual risk  
- `07_reviewer_explanation/guides/`  
- Findings disposition board + findings register  

### D. Sealed run evidence

Minimal machine evidence so a **bare clone** can recheck the controlled release **without** patient data or ODA:

| Artifact | Role |
|---|---|
| `platform/pipeline_health.json` | Run identity (mode, full_dag, GREEN) |
| `platform/reconciliation_status.json` | SAS↔R dataset recon |
| `platform/results_reconciliation_status.json` | Results recon |
| `platform/admiral_reconciliation_status.json` | Third engine |
| `platform/tfl_output_index_status.json` | TFL catalog gate |
| `platform/validation_strategy/validation_strategy_status.json` | Validation control |
| `platform/log_cleanliness/log_cleanliness_status.json` | Log gate |
| `platform/release_run_manifest/release_run_manifest.json` | Hash seal |
| `platform/release_candidate/release_candidate_status.json` | RC checklist |
| `platform/evidence/` | Frozen genuine ODA snapshot (byte-distinct proof) |

Everything else regenerable is **local only**.

---

## 3. What does **not** stay in git (LOCAL / REGENERABLE)

| Class | Examples | Why out |
|---|---|---|
| Patient data | `01_source_data/real_sdtm/*`, all `*.xpt` ADaM/package | Data rights + hygiene |
| Secrets | `_authinfo`, `sascfg_personal.py`, `.env` | Security |
| Build outputs | `04_analysis_datasets/adam/*`, Dataset-JSON bodies | Rebuild from programs |
| Factory telemetry piles | Most `platform/**/*_status.json`, inventory CSVs | Regenerable noise |
| Generated control reports | `docs/*_REPORT.md`, dashboards, gate-map dumps | `build_delivery_controls.py` |
| Dead / one-off code | `tools/archive/**` | Not portfolio face |
| Tool installs | `.core_engine/`, `.p21/`, `renv/library/` | Re-downloadable |
| Runtime caches | `stage_cache.json`, ODA locks, logs | Ephemeral |

Version **code, controlled documents, and sealed evidence**, not transient runtime output.

---

## 4. Reproducibility contract (honest)

| Who | What they can do |
|---|---|
| **Any interviewer (bare clone)** | Read `m5/` + guides; run `scripts/verify_release.py`; run `python3 platform/cibuild.py --demo` |
| **GitHub Actions** | Job `Path A seal verify (verify_release)` reruns `scripts/verify_release.py` on push/PR (no SAS/data) |
| **You with SDTM + ODA/local SAS** | Full dual-language DAG; re-seal; refresh package |
| **Nobody from public git alone** | Re-derive real MP patient-level ADaM without licensed source |

Details: [`00_governance/REPRODUCIBILITY.md`](../00_governance/REPRODUCIBILITY.md).

“Fully reproducible” here means:

1. **Environment** pinned (`renv.lock`).  
2. **Pipeline structure** declared (`study_manifest.yaml`).  
3. **Code** complete for dual-language + package.  
4. **Demo path** works without data.  
5. **Seal re-check** works without re-running ODA.  
6. **Real path** documented when data/credentials exist.

It does **not** mean “every intermediate JSON is in GitHub.”

---

## 5. How to refresh the sealed surface (operators)

After a genuine full run you intend to show:

```bash
python3 platform/cibuild.py --real-sas   # when data + engine available
python3 platform/package_ectd.py
python3 platform/build_delivery_controls.py   # local reports only
python3 scripts/verify_release.py
# Commit only: code changes + seal allowlist + m5 data-free package + release note
```

Do **not** bulk-commit `platform/**/ *_status.json` or regenerable `docs/*_REPORT.md`.

---

## 6. Conflict rule

If a file is useful locally but not on the TRACK list → **gitignore it**.  
If interviewers need it to understand the package → **put it under m5/ or guides**, not as root noise.  
If PRODUCT_CLAIM forbids a claim → no artifact in git may imply that claim.
