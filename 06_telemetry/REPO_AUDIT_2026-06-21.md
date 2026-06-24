# TROPIC Repository Audit — Submission-Readiness Review (2026-06-21)

> [!NOTE]
> **Status (as of 2026-06-23):** Point-in-time record. Its open items are now closed —
> F2 (CORE run aligned to the SDTMIG 3.4 layer) and F3 (the eCTD backbone + materialize
> steps wired into the DAG; pipeline now **22 stages**) were resolved in commits
> 49464a9 / 6f0dac4. References below to a "17-stage" pipeline / "standalone, not in CI"
> additive layer reflect the 2026-06-21 state. Body retained as-authored.

Submission-readiness audit of the repository against FDA/CDISC standards. Audit-first, evidence-based;
only unambiguous doc-only fixes applied this pass (listed in §8); nothing substantive
touched. Honest-disclosure caveats (synthetic arm, single-author validation, sim-vs-real
SAS) are preserved, not polished away.

## 1. Executive summary

The repository is in **strong** shape and, after the terminal-session SDTM 3.4 uplift +
CT 2026-03-27 refresh + eCTD materialization, is **standards-current or ahead almost
everywhere**. The original 17-stage `cibuild.py` pipeline is internally consistent and
CI-gated; all runnable gates pass (§7).

The one real systemic theme is **two construction epochs**: the original CI-gated pipeline,
and a newer capability layer (SDTM 3.4 uplift, eCTD sequence, Dataset-JSON, ARS, USDM,
sensitivity) that is **standalone — not wired into the manifest / `cibuild.py` / CI**. That
layer is genuine and independently verified, but it isn't orchestrated or gated, and the
README had lagged it. The critical README contradiction is fixed; the rest is a small,
ordered backlog (§6), most of it your decision.

Top risks: (P1, fixed) README↔define version contradiction; (P2) the offline CORE script
still validates 3.2 while the package is 3.4; (P2) the additive layer isn't CI-gated.
Nothing here is an FDA technical-rejection trigger in the package's stated demonstration
scope.

## 2. Standards currency (web-verified, June 2026)

| Standard | Current | Repo actual | Verdict |
|---|---|---|---|
| SDTMIG | 3.4 final & FDA-supported (4.0 in public review) | `define_sdtm.xml` 3.4 (uplifted) | current |
| ADaMIG | 1.3 | 1.3 | Yes |
| Define-XML | 2.1 (latest patch 2.1.11) | 2.1.0 | conformant |
| Controlled Terminology | 2026-03-27 (RP61) | 2026-03-27 both defines | current |
| Dataset-JSON | 1.1 (FDA evaluating, FR notice Apr 2025) | 1.1 + XPT | ahead |
| ARS | 1.0 | 1.0 | Yes |
| USDM/DDF | v3 final (v4 in review) | 3.0.0 | Yes |
| CDISC CORE | v0.16.x; **0 executable ADaM rules** | CORE 0.16.0 + custom ADaM rules | (gap is upstream, disclosed) |
| FDA sdTCG | Tech-Specs issued 2025-03-27 | cited | Yes |
| FDA Data Standards Catalog | SDTMIG 3.2/3.3/3.4 supported | repo 3.4 | resolved |
| eCTD | ICH 3.2.2; FDA us-regional v3.3 | ICH 3.2 + STF 2.2 + us-regional 3.3, **DTD-valid** | Yes |
| ICH E9(R1) | estimands, 2020 | step-down pattern | Yes |
| pharmaverse admiral | 1.4 (Jan 2026) | used (3rd track) | Yes |

## 3. Pipeline flow (real, current)

```
raw SDTM (01_raw_source/real_sdtm, v3.1.1, pristine)
  │   └─[standalone] uplift_sdtm_34.R + uplift_define_34.py → SDTM 3.4 derived + define
  ▼
S1–2  staging ingest + R SDTM validation
  ▼
S3–10 per-dataset R validation ×8 (adsl adex adcm adae adlb adrs adtte clinsite)
  │        └─[standalone] admiral_adsl/adtte.R → admiral_reconcile.R (3rd track)
S11   SAS production (ODA / real / SIMULATE sentinel)
  ▼
S12   cross_lang_audit (dataset recon)   S13 TFL (merges synthetic CbzP)
S14   results_reconcile (PROC LIFETEST vs survfit)   S15–16 spec→define / spec→data
S17   package_ectd.py → m5/ dataset tree
  │
  └─[standalone, NOT in CI] build_ectd_backbone.py + materialize_ectd.py → 11_ectd/0000 (DTD-valid sequence)
                            export_datasetjson.py → 10_datasetjson | build_ars.py → 12_ars
                            build_usdm.py → 13_usdm | date_precision_sensitivity.py
                            run_core_conformance.sh (CORE 3.2 + ADaM custom)
```
17 CI stages verified: 2 pre + 8 datasets + 1 SAS + 6 post (`cibuild.py:522`).

## 4. Reconciliation matrix

| # | Finding | Evidence | Category | Sev | Status / fix |
|---|---|---|---|---|---|
| F1 | README SDTM rows said 3.1.1 / "392 SDTMIG-3.2 rules / version-gap" vs define 3.4 | `README.md:359-360` vs `define_sdtm.xml` `Version="3.4"`, `SDRG.md:6,70`, `SDSP §1` | STALE/INCONSISTENT | P1 | FIXED (doc-only) |
| F2 | `run_core_conformance.sh` validates SDTMIG **3.2** against 3.1.1 source while the *packaged* SDTM is 3.4; traceability still says "SDTMIG-3.2 rules" | `run_core_conformance.sh:47`; `TRACEABILITY_MATRIX.md:128` | STALE/INCONSISTENT | P2 | **[needs decision]** point the offline CORE run at the 3.4 layer + update the line |
| F3 | 8 capability scripts + the CORE script are standalone — not in manifest/`cibuild.py`/CI | `cibuild.py:522`; `study_manifest.yaml:74-83`; `.github/workflows/ci.yml` | UNFINISHED (half-wired) | P2 | **[needs decision]** wire deterministic ones into post-stages+CI, or add an "offline runbook" |
| F4 | README standards table omitted the modern layers (Dataset-JSON/ARS/USDM) | `README.md` table | INCOMPLETE | P3 | FIXED (doc-only row, honestly flagged "outside CI") |
| F5 | Two eCTD paths (`package_ectd.py` vs backbone+materialize) | `study_manifest.yaml:83`; `11_ectd/RUN_RECORD.md` | UNDOCUMENTED overlap | P3 | largely covered (README sdTCG row + RUN_RECORD name both); optional 1-line note |
| F6 | ADRS actual rows **3275** (post §4A enrichment) vs **2904** cited in two **historical** records | actual `adrs_prod.xpt`=3275; `CHANGELOG.md:417`, `p21_conformance_runrecord.md:18` | STALE (historical) | P3 | **[needs judgment]** do NOT rewrite history; optional forward-note "ADRS later enriched to 3275". No *authoritative* doc (SDRG/ADRG/define) cites a wrong count |

**Verified clean (non-findings):** "17 stages" accurate; m5 program copies byte-identical to source (no drift); retired files genuinely absent; `uplift_define_34.py` exists (SDRG:70 valid); `admiral_*.R` referenced/documented; no real TODO/FIXME/stubs (3 benign comment matches); core `06_telemetry` helpers all referenced; CT 2026-03-27 real & applied to both defines; ADaM counts (ADSL 371, ADAE 5428, ADCM 24534, ADEX 13052, ADLB 78619, ADTTE 2058, clinsite 69) all match docs; headline N (371/378/749) consistent across docs.

## 5. Regulatory gap table

| Area | Status | Reviewer note | Minimal fix |
|---|---|---|---|
| SDTMIG version | resolved (3.4) | was the TRC risk | F2 aligns the offline check |
| CT currency | 2026-03-27 | — | refresh at lock |
| Define-XML/ARM | 2.1+ARM, referential gates pass | — | optional 2.1.x patch |
| eCTD sequence | DTD-valid, materialized; EXAMPLE IDs | placeholder app numbers (disclosed) | real IDs before submission |
| ADaM business rules | ◑ none exist upstream; custom + interim | disclosed | P21/Certara when licensed |
| Process maturity (CI) | Note: additive layer not gated (F3) | "could rot / regen unclear" | wire-in or runbook |
| Synthetic arm / single-author | ◑ by design, disclosed | not fileable as marketing app | preserve caveats |

## 6. Prioritized remediation backlog

1. F1 — README SDTM rows → 3.4. **[doc-only]** done.
2. F4 — README modern-layers row. **[doc-only]** done.
3. F2 — align `run_core_conformance.sh` to the 3.4 packaged layer + traceability line. **[needs decision — script change]**
4. F3 — orchestrate or document the standalone layer (runbook first cut is low-risk/doc-only; CI wiring is substantive). **[needs decision]**
5. F6 — optional forward-note on ADRS 2904→3275 in the two historical records (do not falsify). **[needs judgment]**
6. F5 — optional one-line note distinguishing the two eCTD paths. **[doc-only]**

## 7. Verification evidence (this pass)

Ran the repo's own gates that are runnable in this environment:

- `validate_define.py define.xml` → **PASS** (324 checks); `define_sdtm.xml` → **PASS** (315).
- `lint_sas.py` → **PASS** (0 errors, 0 warnings across 18 files).
- `validate_core_rules.py` → **PASS** (7 rules, 0 errors).
- eCTD `xmllint --noout --valid` on all 3 backbone files → **DTD-VALID** (re-confirmed independently).
- Ground truth: `define_sdtm.xml` SDTMIG **3.4**, CT **2026-03-27**; `define.xml` ADaMIG 1.3; m5 in-sequence SDTM define **3.4**; us-regional namespace `http://www.ich.org/fda` dtd-version 3.3.
- ADaM row counts read from XPT and reconciled to docs (only ADRS differs from the two historical records — F6).

**Honest limitation:** `Rscript` is **not available in this sandbox**, so the R-based gates
(`check_define_conformance.R --self-test`, `spec_data_checks.R`, R lint, `cibuild.py --demo`,
the R reconciliations) could **not** be executed here. They should be run in the R
environment before relying on them; this audit did not independently re-run them.

## 8. Changes applied this pass (doc-only, surgical)

- `README.md:359-360` — the two SDTM conformance rows now state SDTMIG **3.4 (uplifted from
  3.1.1 source)** + the CORE-at-3.4 run, matching `define_sdtm.xml`/SDRG/SDSP, with the
  source/uplift framing preserved. (Applied in the prior pass; re-confirmed intact.)
- `README.md` — added one standards-table row enumerating the modern machine-readable
  layers (Dataset-JSON / ARS / USDM), explicitly noting they are produced **outside** the
  17-stage CI pipeline (surfaces F3 honestly rather than overstating).
- `06_telemetry/REPO_AUDIT_2026-06-21.md` — this report (new).

No code, data, define, manifest, or CI changes. F2/F3 (substantive) await your decision.

## 9. Full orphan sweep (every file, added 2026-06-21)

Walked all **605 files** (excl. vendored `.git`/`renv`/`.core_venv`/`.core_run`/`.core_engine`);
**203 connectable** code/doc/config/metadata files reference-checked. Results:

**Connected (false positives cleared):** `conformance_rules/adam/TROPIC-ADAM-10[1-7].yml`
are loaded by **directory** (`run_core_conformance.sh:56 -lr .../conformance_rules/adam`),
not by filename — not orphans. `guyot_digitised/*_wpd_raw.csv` are **intentionally-retained
raw WebPlotDigitizer exports** for provenance (the pipeline reads the cleaned
`*_digitised.csv`/`*_nrisk.csv` per `reconstruct_cbzp_guyot.R:33-36`) — by design.
Tooling/meta (`.claude/*`, `.vscode/*`, `CLAUDE.md`) and `reference_literature/` are not
pipeline files.

**Genuine loose ends (new findings, all P3 / cleanup — none correctness or submission-blocking):**

| # | Finding | Evidence | Category | Fix |
|---|---|---|---|---|
| F7 | `02_production_sas/utilities/GIT_RESCUE.sas` — a SAS state-reset/lock-release dev snippet ("QUOTE & MACRO KILLER BLOCK"), referenced nowhere, not in any program flow | basename refs = 0 (excl self) | HANGING/dead | **[needs decision]** remove, or move to a documented `dev/` + note in README |
| F8 | `07_define_xml/remediate_sdtm_define.py` — one-time lxml define-remediation tool, undocumented and unreferenced; functionally superseded by `uplift_define_34.py` | basename refs = 0; `uplift_define_34.py` now does define uplift | REDUNDANT/HANGING | **[needs decision]** document as historical one-shot, or remove |
| F9 | Three session audit reports (`ADDITIVE_INTEGRATION_SCAN_2026-06-20.md`, `FDA_REVIEWER_AUDIT_2026-06-20.md`, `REPO_AUDIT_2026-06-21.md`) were not linked from any index; `reference_literature/TROPIC STDM Define.xml` had a filename typo (STDM→SDTM) | not referenced | HANGING (docs) / cosmetic | **FIXED** — reports indexed in README "Audit & review records"; file renamed to `TROPIC SDTM Define.xml` |

**F7/F8 disposition (your decision: option c):** left in place, not removed. `GIT_RESCUE.sas` and `remediate_sdtm_define.py` remain as-is (potential dev/historical tools); revisit if a cleanup pass is wanted later.

Everything else connects: 17-stage pipeline, admiral 3rd track, reviewer-guide cross-refs,
m5 program copies (byte-identical), and the standalone additive layer (its non-wiring is
F3, already logged). No undocumented program file remains except F7/F8.
