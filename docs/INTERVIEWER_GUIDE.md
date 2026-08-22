# Interviewer Guide — 10 minutes

**What this repo is:** a controlled **clinical-submission simulation** with executable evidence boundaries
(not an FDA filing, not Part 11, not a re-analysis of trial efficacy).

**Binding claim:** [`PRODUCT_CLAIM.md`](PRODUCT_CLAIM.md)

---

## Minute 0–2 — Claim

Open:

1. Root [`README.md`](../README.md)
2. [`PRODUCT_CLAIM.md`](PRODUCT_CLAIM.md)

You should hear:

- Real MP arm (N=371) SDTM → dual SAS/R ADaM + recon
- Synthetic CbzP for TFLs only
- Module 5–style package + hash-sealed demo RC
- Single-author tracks ≠ org GxP double programming

---

## Minute 2–6 — Review package (what we want you to see)

Open **only**:

```text
08_submission_package/m5/datasets/tropic/
  tabulations/sdtm/     # define + SDRG (+ blank CRF)
  analysis/adam/        # define + ADRG + programs
  bimo/                 # clinsite + BDRG
08_submission_package/m5/53-clin-stud-rep/.../tropic/
  figures/  tables/     # controlled TFL set
```

Tour doc: [`../08_submission_package/README.md`](../08_submission_package/README.md)

Visual review surfaces:

- [`../05_outputs/tfl/TFL_Gallery.html`](../05_outputs/tfl/TFL_Gallery.html) — portable static figure gallery
- [`../06_qc_evidence/audit/DASHBOARD_VISUAL_QC.md`](../06_qc_evidence/audit/DASHBOARD_VISUAL_QC.md) — five-tab dashboard acceptance evidence
- `../07_reviewer_explanation/tools/shiny/app.R` — read-only local dashboard source; authorized local production inputs are required for the data-bearing view

Guides (markdown sources):

- [`../07_reviewer_explanation/guides/ADRG.md`](../07_reviewer_explanation/guides/ADRG.md)
- [`../07_reviewer_explanation/guides/SDRG.md`](../07_reviewer_explanation/guides/SDRG.md)
- [`../07_reviewer_explanation/guides/BDRG.md`](../07_reviewer_explanation/guides/BDRG.md)

**Patient-level XPT is not in git** (standard data hygiene). Structure, define, programs, and TFLs are.

---

## Minute 6–8 — Factory spine (if they ask “how is it built?”)

Do **not** open random `platform/*_status.json`.

Open:

| File | Role |
|---|---|
| [`SCRIPT_MAP.md`](SCRIPT_MAP.md) | What runs vs ignore |
| [`../config/study_manifest.yaml`](../config/study_manifest.yaml) | DAG shopping list |
| [`../platform/cibuild.py`](../platform/cibuild.py) | Orchestrator |
| `04_analysis_datasets/programs/sas/A_adsl_generation.sas` | Production example |
| `04_analysis_datasets/programs/r/v_adsl_validation.R` | Validation example |
| `06_qc_evidence/reconciliation/cross_lang_audit.R` | SAS↔R proof method |

Factory triage: [`../platform/README.md`](../platform/README.md)

---

## Minute 8–10 — Seals & residual honesty

```bash
python3 scripts/verify_release.py
python3 platform/check_submission_readiness.py
```

On the current public branch, the readiness profile is intentionally
**BLOCKED** and the release verifier stops on stale source/artifact hashes.
That is the correct result until an authorized full SAS/ODA run refreshes the
controlled seal; do not present this branch as FDA-ready or as a green filing
release.

Also open:

- [`RELEASE_NOTE_v0.3.0-clinical-simulation.md`](RELEASE_NOTE_v0.3.0-clinical-simulation.md)
- [`QUALITY_SYSTEM_BOUNDARY.md`](QUALITY_SYSTEM_BOUNDARY.md)
- [`FDA_READINESS_RESEARCH_2026-08-15.md`](FDA_READINESS_RESEARCH_2026-08-15.md)
- [`workstreams/WS5_KNOWN_DIFFERENCES_MEMO.md`](workstreams/WS5_KNOWN_DIFFERENCES_MEMO.md)
- Frozen ODA snapshot: `platform/evidence/`

---

## What we intentionally do **not** show as “the product”

| Noise | Why ignored in interview |
|---|---|
| Regenerable `docs/*_REPORT.md` | Control printers, not ADRG |
| Most factory status JSON piles | Local run telemetry |
| `studies/DEMO02` | Multi-study engine proof only |
| Dataset-JSON / ARS / USDM deep dive | Additive pilots, not Module 5 primary |
| Dead code | Not in portfolio surface |

Policy: [`REPO_SURFACE_POLICY.md`](REPO_SURFACE_POLICY.md)

---

## Bare-clone reproducibility (no data)

```bash
git clone <url> && cd TROPIC
python3 scripts/verify_release.py      # seal re-check
python3 platform/cibuild.py --demo     # smoke: syntax + recon method
```

Full dual-language rebuild requires licensed SDTM + SAS (ODA or local) — see
[`../00_governance/REPRODUCIBILITY.md`](../00_governance/REPRODUCIBILITY.md).
