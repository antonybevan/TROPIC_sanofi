# Changelog

All notable changes to the **TROPIC (Study EFC6193 / XRP6258)** pipeline will be documented in this file. This log serves as the program version control history, in support of 21 CFR Part 11 electronic records auditing.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to Semantic Versioning.

## [3.13.0] - 2026-06-18 — PCWG3-correct integrated RECIST response + bone 2+2, verified on real SAS

> **Context.** Two linked changes, both proven on a **genuine `oda`-mode run** (real SAS 9.4 on
> ODA, endpoint `odaws01-apse1-2`, SDTM manifest `329430f6…`, `probe_nonce_echoed = true`):
> Finding **B**'s integrated overall-response derivation, and a SAS character-length fix that the
> **real** SAS↔R reconciliation surfaced — a discrepancy `sim` mode is structurally blind to.

### Added
- **Integrated RECIST overall response (`OVRLRESP`)** in both tracks (`A_adrs_generation.sas`,
  `v_adrs_validation.R`): a new lesion ⇒ auto-PD; non-target PD ⇒ PD; target CR with non-target
  non-CR ⇒ PR; with a defensive target-only fallback. 648 `OVRLRESP=PD` records now reflect
  non-target / new-lesion progression that target-only logic missed.
- **Bone Scan Progression (`PARAMCD = BSGRESP`)** — PCWG3 **2+2** rule (Scher 2016), 3-level
  `AVALC`: `PROGRESSION` / `PROGRESSION UNCONFIRMED` / `NO PROGRESSION`. Confirmed `PROGRESSION`
  is the only state that feeds `TTUMOR` (the `A_adtte` PD-date logic already expected this slot).
  Thresholds (`BONE_PROG_MIN_NEW`, `BONE_PROG_CONFIRM_NEW`) are config-driven via `study_config.yaml`.
  On the real MP arm the strict 2+2 yields **5 PDu / 0 confirmed** — reported honestly, not tuned.

### Changed / Fixed
- **`AVALC` truncation fixed (real-SAS reconciliation catch).** In `data work.adrs_union; set …
  work.bsgresp;` the `AVALC` length was fixed by the first contributing dataset (`$20`), silently
  truncating `'PROGRESSION UNCONFIRMED'` (23 chars) to `'PROGRESSION UNCONFIR'`. The Stage-12
  cross-language audit flagged **5 `BSGRESP` cells** (SAS vs R). Fix: `length AVALC $100;` before
  the SET — matching `define.xml IT.ADRS.AVALC Length=100`. This is a defect `sim` mode could
  never have shown (its zero-diff is a byte-copy tautology); only an independent SAS engine exposes it.
- **Stage 14 (numerical results reconciliation, SAS vs R) closed.** Previously `not_available`
  (no real `PROC LIFETEST` stats existed); now **PASS** on all 6 parameters (OS, PFS, TTPAIN,
  TTPSA, TTSAE, TTUMOR). Full 17-stage pipeline GREEN; dataset reconciliation **8/8 PASS**
  (ADRS FAIL→PASS). Expected downstream shifts confirmed: MP ORR 7.9%→**6.4%** (measurable),
  TTUMOR median 2.3→**2.1 mo**; TTPSA unchanged.
- **GREEN-ODA evidence badge refreshed** (`06_telemetry/evidence/`, audit C-1): the immutable
  snapshot + `*_prod`/`*_v` md5 manifest now certify this current ADRS code, not the pre-Finding-B run.
- **ADRG §4A** documents the integration matrix, the PCWG3 2+2 rule, and the honest 5-PDu/0-confirmed
  result; §4 (`TTUMOR`), README and the traceability matrix updated; m5 copies + `adrg.pdf` resynced.

## [3.12.0] - 2026-06-17 — ARM expansion to all analysis displays

> **Context.** Analysis Results Metadata (ARM v1.0) previously covered only the 3 survival/
> secondary/TEAE ResultDisplays; the exploratory figure displays and the lab-shift table had no
> ARM. This release extends ARM to **every analysis display** so each has result→method→ADaM
> dataset/variable traceability. Pure `define.xml` authoring — no new dependencies.

### Added
- **5 new ARM ResultDisplays / AnalysisResults** in `07_define_xml/define.xml` (ARM now
  **8 ResultDisplays / 10 AnalysisResults**):
  - `RD.EFFICACY.SUBGROUP` / `AR.OS.SUBGROUP` — OS prognostic-subgroup forest (figure **F-12-1**).
  - `RD.EFFICACY.PSA.RESPONSE` / `AR.PSA.BESTPCHG` — PSA best % change waterfall (**F-13-1**).
  - `RD.SAFETY.EXPOSURE` / `AR.TRTDUR.EXPOSURE` — treatment-exposure swimmer (**F-14-1**).
  - `RD.OPTIMUS.ER` / `AR.OPTIMUS.RDI.ANC` — Project Optimus RDI vs ANC-nadir scatter (**F-17-1**).
  - `RD.SAFETY.LABSHIFT` / `AR.LAB.SHIFT` — CTCAE grade shift baseline→worst (table **T-21-1**).
- Each `ResultDisplay` names its TFL ID for ARM↔TFL traceability and links the exact ADaM
  datasets/variables (+ value-level `WhereClauseRef`s) and the analysis method/programming code.

### Changed / Fixed
- **Verified:** define.xml still **XSD VALID** (Define-XML 2.1 + ARM v1.0); `validate_define.py`
  referential-integrity gate **PASS (324 checks**, up from 284 — every new ARM `ParameterOID` /
  `ItemGroupOID` / `AnalysisVariable.ItemOID` / `WhereClauseOID` resolves); spec→define gate
  unaffected. CONSORT disposition (F-01) and the discontinuation listing (L-01) are intentionally
  out of ARM scope (flow diagram / listing, not analysis results).
- **ADRG §6** and the traceability matrix updated to reflect full ARM coverage.

## [3.11.0] - 2026-06-17 — Specification → define inversion (audit C-4 fixed)

> **Context.** Closes audit finding **C-4** for real. The previous "spec"
> (`ADaM_Define_Extract.xlsx`) was rendered *from* `define.xml` on every build — a circular,
> zero-verification traceability inversion. This release makes an authoring-format ADaM
> specification the **single source of truth** and checks the define + the produced data
> *against* it, using the pharmaverse **metacore / metatools / xportr** toolchain. The previous
> remediation only *reframed* the extract honestly; this one actually *inverts* the direction.

### Added
- **Authoritative ADaM specification** `00_specifications/ADaM_spec.xlsx` (CDISC / Pinnacle-21
  metacore workbook: Study, Datasets, Variables, ValueLevel, WhereClauses, Codelists, Methods).
  Loadable via `metacore::spec_to_metacore()` (`03_validation_r/load_spec.R`). Bootstrapped once
  by `00_specifications/build_spec_seed.R` (documented one-time migration), human-edited master after.
- **spec → define conformance gate** `07_define_xml/check_define_conformance.R` — asserts every
  dataset/variable/label/type/length/order/mandatory/codelist/method in `define.xml` matches the
  spec; exits non-zero on drift. Ships a `--self-test` that injects synthetic drift and confirms
  detection (proves the gate is not a no-op). Latest run **PASS** (7 datasets / 157 variables).
- **spec → data conformance gate** `03_validation_r/spec_data_checks.R` — checks the produced
  `04_adam/*_prod.xpt` against the spec with `metatools::check_variables` / `check_ct_data` and
  `xportr::xportr_type`/`xportr_length`. Independent (non-circular) verification. Latest run
  **PASS** across all 7 datasets. Reports in `06_telemetry/conformance/spec_{define,data}_conformance.json`.
- Pipeline **Stages 15–16** (cibuild) and a CI step run both gates; `metacore`, `metatools`,
  `writexl` added to `renv.lock`.

### Changed / Fixed
- **Variable-label artifacts are now spec-sourced.** `06_telemetry/gen_adam_labels.R` derives
  `03_validation_r/adam_var_labels.csv` (R track) and `02_production_sas/_adam_labels.sas` (SAS
  track) from the spec — replacing the define-sourced `gen_adam_labels.py`. Label content is
  **byte-identical** to before (no output regression); only the provenance flips define → spec.
- `package_ectd.py` now ships `ADaM_spec.xlsx` + the spec→define conformance report instead of
  the retired extract. eCTD packaging is now Stage 17 (was 15).
- **Retired** `06_telemetry/generate_adam_specs.py`, `06_telemetry/gen_adam_labels.py`, and
  `00_specifications/ADaM_Define_Extract.xlsx` (the circular define → extract path).
- **ADRG §6.1** added documenting the inversion and the two gates.

## [3.10.0] - 2026-06-17 — CDISC CORE conformance + Define-XML hardening

> **Context.** Ran the **official CDISC reference engine (CORE 0.16.0)** against the project's
> SDTM and ADaM — the real business-rule layer the home-grown `adam_conf_check.R` stood in for —
> and fixed the Define-XML defects CORE surfaced. Honest headline finding: **CORE/CDISC Library
> ships 0 executable ADaM rules** (confirming, not refuting, ADRG §6), so executable ADaM rules
> are authored in CORE format and run via `--local-rules`.

### Added
- **Executable ADaM conformance rules in CORE YAML** (`06_telemetry/conformance_rules/adam/`,
  7 rules across all 7 ADaM datasets) run via CORE `--local-rules` → **7/7 SUCCESS** with the
  Define-XML engaged (`Define_XML_Version 2.1.0`). Fills the gap where CDISC ships no ADaM pack.
- **CORE runner** (`06_telemetry/run_core_conformance.sh`) — reproducible setup (venv, engine,
  library-metadata cache via `CDISC_LIBRARY_API_KEY`, SDTM XPT conversion, SDTM + ADaM runs).
- **CI gate** (`06_telemetry/validate_core_rules.py`) — rule-pack well-formedness check (no API
  key/data needed), wired into `.github/workflows/ci.yml`.
- **CORE run evidence** (`06_telemetry/conformance/`) — `CORE_RUN_RECORD.md` + redacted SDTM/ADaM
  JSON reports (per-record subject-level `Issue_Details` stripped).

### Changed / Fixed
- **Define-XML now parses in CORE (both files), root-caused and fixed.** CORE's reader failed with
  `'NoneType' object has no attribute 'Name'` because no `ItemGroupDef` declared a `def:Class`.
  Added `def:Class` (correct position, valid enumeration) to all **16 SDTM + 7 ADaM** datasets;
  also removed an invalid `Role` attribute (`ItemGroupDef`) and populated 16 empty `TranslatedText`
  descriptions in `define_sdtm.xml`. Both defines **still pass XSD** and now read in CORE at 2.1.0.
- **SDTM CORE run:** 392 SDTMIG-3.2 rules executed (15 issue-reporting / 47 finding rows);
  documented the **SDTMIG 3.1.1-vs-3.2 version-gap** caveat — a real engine run, not a clean pass.
- **ADRG §6** updated with the 2026-06-17 CORE re-verification and the Define-XML parse fix.

### Notes
- The official **CDISC ADaM Conformance Rules v4.0/v5.0** (for an `AD####` ID crosswalk) are
  **members-only** (Library API returns "Members-only content" on a free key); rule IDs here are
  `TROPIC-ADAM-###` placeholders pending a membership account. CORE engine/venv/cache and any
  converted XPT stay under gitignored `.core_run/` / `.core_venv/` (never committed).

## [3.9.0] - 2026-06-16 — Audit remediation: status integrity, BIMO, evidence badge

> **Context.** Post-audit hardening pass (findings C-1…C-6). Verified end-to-end on a **genuine
> ODA run**: `sas_execution_mode = oda`, all **15** stages GREEN, dataset reconciliation PASS
> (**8/8** domains incl. CLINSITE), results reconciliation PASS (6/6 parameters), SAS log 0 ERROR.

### Added
- **Committed GREEN-ODA evidence badge (`06_telemetry/evidence/`, C-1).** Immutable snapshot of a
  real `oda`-mode run (pipeline_health, both reconciliation verdicts, and an md5 manifest showing
  every `*_prod.xpt` (SAS) is byte-distinct from its `*_v.xpt` (R) yet reconciles cell-identical).
  Stored separately from live telemetry so a later `sim` run can never clobber the proof.
- **BIMO Data Reviewer's Guide (`08_reviewers_guides/BDRG.md`, C-5).** Documents the `clinsite`
  scope honestly against the FDA BIMO TCG Appendix-3 (~39-var) structure, the synthetic-PI
  disclosure, and the ICH E9 population definitions.

### Changed / Fixed
- **Status integrity (C-2).** Results-reconciliation no longer reports a false `PASS` when it legitimately
  no-ops (sim/cached run with no SAS `PROC LIFETEST` stats); it now records `SKIPPED`, and a SKIPPED
  stage keeps the pipeline GREEN without claiming a verification that did not happen.
- **Gate wiring (C-3).** Post-execution gates are keyed by stage NAME, not positional id, so the
  M-4 output-sanity gate fires immediately after TFL rendering again (it had drifted onto the
  packaging stage during a renumber) — corrupted tables are caught before results-recon/packaging.
- **BIMO `clinsite` (C-5).** Expanded to a credible, honestly-derived site-level set
  (`N_RAND/N_SAF/N_ITT/N_PPROT/N_DEATH/N_SAE/N_TEAE`); ITT is no longer mislabelled "Efficacy
  Population"; the synthetic `INVNAM` is explicitly flagged; export uses the proven `&PROJ_ROOT.`
  XPORT idiom (the prior `&adam_path.` macro was undefined and would have failed on real SAS).
  Now double-programmed SAS↔R as the 8th reconciled domain.
- **Define-XML extract (C-4).** The define-derived workbook is renamed `ADaM_Define_Extract.xlsx`
  and carries a provenance sheet stating it is a reviewer-facing VIEW of `define.xml`, not the
  governing specification (removing the spec↔define traceability inversion); spec→define generation
  is documented as roadmap.
- **SAS static analysis (C-6).** Reframed honestly (advisory warnings vs. blocking errors), and
  wired into CI as a real gate (`.github/workflows/ci.yml`) so the blocking-error class cannot regress.

## [3.8.0] - 2026-06-16 — Automated eCTD Module 5 Packaging

> **Context.** Realizing full compliance with eCTD Module 5 structure. This release implements an
> automated packaging orchestrator script to compile the functional pipeline components (datasets,
> programs, metadata, generated PDF reviewer guides, and CSR with outputs) into a canonical FDA eCTD
> Module 5 directory structure.

### Added
- **eCTD Module 5 packaging orchestrator (`06_telemetry/package_ectd.py`).** Dynamically compiles SDTM datasets into v5 `.xpt` files, copies/renames ADaM datasets to strip `_prod` suffixes, generates PDF formatted reviewer guides (ADRG/SDRG) and CSR (with outputs in appendices), creates a blank CRF placeholder, and co-locates Define-XML metadata files.
- **Git protection for deliverables.** Added `m5/` directory to `.gitignore` to ensure the generated eCTD package remains an ephemeral build artifact.

## [3.7.0] - 2026-06-16 — Results-level double-programming, confirmed ORR, output gate

> **Context.** Post-audit hardening. Double-programming now extends from the ADaM dataset
> layer to the analysis-results layer; the response derivation is corrected to the published
> confirmed rate; and a deliverable sanity gate prevents code artifacts reaching a table.
> Verified on a real ODA run: all **13** stages GREEN, dataset reconciliation PASS (7/7
> domains), results reconciliation PASS (6/6 parameters).

### Added
- **Numerical results reconciliation (Stage 13, `05_reconciliation/results_reconcile.R`).** SAS
  computes MP-arm survival statistics independently with `PROC LIFETEST` (KM median / events / N),
  exported to `tte_stats_prod.csv`; R recomputes with `survival::survfit` and the two are diffed
  numerically (median tol 1 day; events/N exact). Verdict in `results_reconciliation_status.json`
  gates the build; degrades to `not_available` in sim mode. Two-arm HR (synthetic CbzP) stays
  R-only by construction and is labelled as such.
- **Deliverable sanity gate (Stage 12, `cibuild.py::output_sanity_check`).** Fails the build if a
  published table/listing contains lint pragmas, unrendered `sprintf` specs, or `<NA>`/`NaN`/`Inf`.
- **Committed `.lintr`** pinning the R style standard (line length 120; CDISC-uppercase, dplyr-NSE,
  mixed-pipe and explicit-return exemptions justified inline) + a **CI lint gate** in `ci.yml`. Lint
  is now reproducibly **0** across production/validation/reporting R.

### Changed / Fixed
- **ORR now requires RECIST v1.0 confirmation (M-2)** in `A_adrs_generation.sas` + `v_adrs_validation.R`
  (a CR/PR confirmed by a later CR/PR ≥ `RECIST_CONFIRM_DAYS` = 28 d). Real-MP ORR drops from the
  unconfirmed **18.2%** to **7.9%** (measurable) / **4.6%** (response-evaluable) — close to the
  published 4.4%. define.xml `OBJRESP` decode updated to match.
- **ADTTE negative-time anomalies surfaced (MO-4):** event/censor dates preceding the time origin are
  still floored to 1 day but now emit an explicit per-subject warning in both tracks (SAS `putlog`,
  R `warning()`) instead of being silently masked.
- **`define.xml` `AsOfDateTime` is hash-gated (Mi-02):** restamped only when metadata content actually
  changes, not on every run (removes misleading provenance churn). Repo git identity configured.
- **CDISC accuracy:** "OCCDS v1.1" corrected to **OCCDS v1.0 + custom episode-merging extension**
  throughout (no CDISC OCCDS v1.1 standard exists); the merging rule is labelled a TROPIC convention.
- **TFL deliverable fix:** removed leaked `# nolint` pragmas from `T-11-Efficacy_Tables.txt` (root
  cause in the `efficacy_tables` `sprintf` string; now wrapped in a scoped `# nolint` block).
- **Docs aligned** (ADRG/SDRG/README/ANALYSIS_REPORT/TRACEABILITY) to the above, incl. TTE analysis
  conventions (+1-day duration, per-parameter time origin) documented in ADRG §4.1.

## [3.6.2] - 2026-06-14 — ADaM conformance remediation (129 findings → 0)

> **Context.** With CORE shipping no ADaM rules and Pinnacle 21 Community 4.1.0 engine-expired under
> this environment's clock (`06_telemetry/p21_adam_runrecord.md`), a transparent **ADaMIG v1.3-aligned
> conformance gate** (`06_telemetry/run_adam_conformance.sh`) was built to run in-environment. Its
> first pass returned **129 findings (116 Error, 13 Warning)** — real metadata-conformance gaps that
> value-level `diffdf` reconciliation cannot see. This release fixes **all** of them.

### Fixed — define.xml (`07_define_xml/define.xml`, still XSD-valid + 273 referential checks)
- **Variable-name mismatches vs data:** ADLB `lbdy` → **`LBDY`**, ADRS `VISIT` → **`AVISIT`**.
- **`CL.PARAMCD` completed:** added the **33** missing PARAMCD coded values (ADEX/ADLB/ADRS) with
  real PARAM decodes — 14 → **47** terms; clears all "value not in codelist" errors.
- **Lengths corrected:** ADCM `CMTRT` 100 → **200**, ADAE `AESEV` 2 → **10** (data no longer overflows).
- **Metadata accuracy:** ADAE `CIAEDUR` label units **(Days) → (Months)** (matches the `/30.4375`
  derivation); ADSL `DOCPROG` label shortened to ≤ 40 chars.

### Fixed — variable labels applied symmetrically in **both** tracks (was the bulk: 109 findings)
- ADaM datasets previously shipped almost unlabelled (ADSL 3/42 labelled). A single label spec is now
  **generated from define.xml** (`06_telemetry/gen_adam_labels.py`) and applied in both tracks:
  - **SAS production:** `%lbl_<ds>` macros (`02_production_sas/_adam_labels.sas`) applied in
    `U_xpt_export.sas` before XPT export.
  - **R validation:** `config_study.R::write_xpt_v` applies the same labels (`03_validation_r/adam_var_labels.csv`).
  - Result: **155/155 variables labelled** in every `*_prod.xpt` and `*_v.xpt`.

### Verified (real `oda` run)
- **ADaM conformance gate: PASS — 0 Error / 0 Warning** (was 116/13); `06_telemetry/adam_conformance_report.md`.
- Labels changed no values: **reconciliation still zero-diff** across all 7 domains; SAS log remains
  **0 ERROR / 0 WARNING** (the label statements reference only existing variables); pipeline **GREEN**.

## [3.6.1] - 2026-06-14 — First verified real-ODA execution + literally-clean logs

> **Verification scope (read first).** Unlike 3.6.0, this entry was produced by an **actual
> `--real-sas` run on SAS OnDemand for Academics (ODA)** — endpoint `odaws01-apse1-2.oda.sas.com`,
> live nonce-probe verified, against the verified-resident SDTM (manifest `329430f6…`). Recorded
> `sas_execution_mode` is **`oda`**. The SAS↔R reconciliation therefore ran on **real SAS 9.4
> output** (not the sim byte-copy): all **7 ADaM domains report zero cell-level differences**
> (`diffdf`). That single run does two things at once — it **resolves the 3.6.0 verification-scope
> caveat** (the two-track equivalence asserted there is now executed and confirmed), and it **proves
> the log-hygiene edits below changed no values** (a value change would have broken the zero-diff).
> ADaM record counts are unchanged: ADSL 371, ADEX 13052, ADCM 24534, ADAE 5428, ADLB 78619,
> ADRS 2904, ADTTE 2058.

### Fixed — SAS 9.4 log hygiene (master log now **0 ERROR · 0 WARNING · 0 flagged NOTE**)
- **Uninitialized-variable bug (`A_adtte_generation.sas`).** A duplicated keyword in the TTE
  `format ADT STARTDT format yymmdd10. …` statement made SAS create a phantom, never-set variable
  `FORMAT` → *"NOTE: Variable FORMAT is uninitialized."* Removed the stray `format`. The phantom var
  was intermediate (excluded by the final `keep=`), so output is unchanged.
- **Partial-date `INPUT` notes (`S_sdtm_mapping.sas` ×14, `A_adsl`/`A_adtte` PAINBL).** Imprecise
  SDTM `--DTC` values (e.g. `2007-02`, `----07`, single-digit days) hit `input(substr(…),yymmdd10.)`
  → *"Invalid date value"* + *"Invalid argument to function INPUT."* Added the single **`?` informat
  modifier**. Confirmed on ODA to be **value-identical** to the bare informat (partial → missing,
  `2008-02-5` → `2008-02-05` preserved) while suppressing both notes. *(The DATA-step `??` modifier
  is rejected by the PROC SQL `INPUT` function — `ERROR 22-322` — so the SQL-compatible single `?`
  is used.)*
- **"Operation on missing values" notes (×3), output-preserving guards.** ADAE episode duration
  `CIAEDUR` and the gap-window comparison (`A_adae_io_respec.sas`), the ADLB baseline analysis-window
  distance (`A_adlb_generation.sas`), and the ADTTE cycle baseline-diff (`A_adtte_generation.sas`)
  each performed arithmetic on legitimately-missing dates. Guarded so the result (missing) is
  identical; the episode gap-window uses a temp-variable form that preserves the **exact**
  missing-comparison semantics rather than a guard that could shift episode-merge control flow.

### Fixed — R validation log hygiene (now **0 warnings** across all 9 `logrx` logs)
- **`xportr_write` underscore false-positive.** `xportr` flagged the underscore in the deliberate
  `<domain>_v.xpt` validation member name (a check stricter than the SAS v5 transport spec). Added a
  centralized **`write_xpt_v()`** wrapper in `config_study.R` that muffles **only** that exact
  message (`grepl("non-ASCII, symbol or underscore")`); every other xportr warning still surfaces.
  Updated the 7 validation call sites.

### Verified
- 12/12 stages **PASS**; `pipeline_health.json` **GREEN** (`sas_execution_mode: oda`,
  `probe_nonce_echoed: true`); `reconciliation_status.json` **PASS** (7/7 domains zero-diff).
- SAS master log audit: 0 `ERROR`, 0 `WARNING`, 0 `Invalid date value`, 0 `Invalid argument to
  function INPUT`, 0 `uninitialized`, 0 `operation on missing values`, 0 type-conversion notes.
- All 7 `*_prod.xpt` are byte-distinct from the R `*_v.xpt` (genuine independent SAS output, not a
  sim byte-copy) yet agree cell-for-cell under `diffdf`.

## [3.6.0] - 2026-06-13 — Validation-core correctness remediation (portfolio audit roadmap #2–#10)

> **Verification scope (read first).** Every change below is symmetric across the SAS production
> and R validation tracks and was statically verified locally: all pipeline R scripts parse
> (`tests/smoke_test.R`), `define.xml` still passes full XSD validation + the referential gate
> (273 checks), the broker/seed unit tests (10) pass, and the new TFL-stats snapshot test passes.
> The SAS track and the SAS↔R reconciliation were **not executed against a SAS engine** (none is
> available in this environment); the two-track equivalence of these edits is confirmable only on a
> real `--real-sas` (`oda`/`local`) run. Recorded `sas_execution_mode` is still `sim`.
>
> **[Resolved in 3.6.1, 2026-06-14]** — that real `oda` run has since been executed: all 7 ADaM
> domains reconcile zero-diff against real SAS 9.4 output. See the 3.6.1 entry above.

### Fixed — two-track equivalence defects (were masked by sim-mode reconciliation)
- **ADTTE population filter parity.** The R validation track applied **no** analysis-population
  filter while the SAS track filtered `SAFFL='Y'` on every parameter. The tracks were not logically
  equivalent; a real reconciliation would have diverged on any `SAFFL='N'` subject. Both tracks now
  apply identical, explicit population rules per parameter (see *Changed → ITT*).
- **Same-day pain aggregation parity.** SAS used `min()`, R used `first()` for multiple same-day
  pain scores. Standardised on **`min()`** (order-independent, deterministic) in both tracks.

### Changed — ADTTE derivation (`A_adtte_generation.sas` + `v_adtte_validation.R`)
- **ITT vs Safety population, made explicit and carried on-record (#4).** OS & PFS now analysed on
  **ITT** (`ITTFL='Y'`, randomisation anchor) instead of Safety; TTSAE/TTPAIN/TTPSA on Safety;
  TTUMOR on Safety ∩ measurable-disease. `ITTFL` and `SAFFL` are now carried on every ADTTE record.
- **PSA-progression censoring re-sourced from ADaM (#3).** Censor date now comes from **ADLB**
  (`PARAMCD='PSA'`), the same ADaM source in both tracks — previously SAS read raw `sdtm.lb` while
  R read staging `lb.rds` (a built-in mismatch and a break of ADaM-from-ADaM traceability).
- **Data cutoff applied consistently (#10).** `&STUDY_CUTOFF_DT.` now caps the censoring branch of
  **every** TTE parameter (was TTPSA/TTUMOR only).
- **R track de-transliterated (#5).** ADTTE QC restructured around an ordered branch label +
  a single `finalize_tte()` contract rather than mirroring the SAS `if/else` line-for-line. Output
  remains identical by design (the reconciliation target); single-author independence limits noted
  in ADRG §6.

### Added
- **BDS/OCCDS metadata (#7):** ADTTE gains `PARAMN`, `PARCAT1`, `AVALU` (+ the population flags
  above); **ADLB** now carries `ADT` (analysis date); **ADAE** now carries `TRTA`/`TRTAN`. All added
  symmetrically in SAS + R + `define.xml` (XSD-valid).
- **ARM expanded (#7):** from 1 result display to **3** (added *Secondary Time-to-Event Analyses*
  for TTPSA/TTUMOR and *TEAE Summary* for ADAE), 5 `AnalysisResult`s, with the backing WhereClauses.
- **TFL survival-stats snapshot test (#8):** `tests/test_tfl_stats.R` locks the stratified Cox /
  log-rank recipe (extracted to `09_tfl/tfl_stats.R`, shared with `tfl_generation.R`) against
  deterministic fixtures; wired into `cibuild.py --demo`.
- **Pinnacle 21 / CDISC CORE runbook (#9):** `07_define_xml/P21_RUNBOOK.md` (turn-key commands;
  the business-rule layer remains data-gated and is not faked).
- **Portfolio visibility (#6):** the rendered TFL gallery (`09_tfl/output/tables/` and `09_tfl/output/figures/`) and the execution
  evidence (`pipeline_health.json`, `reconciliation_status.json`) are no longer git-ignored, so a
  reviewer sees the figures/tables and the honest `sas_execution_mode` without a local run.

### Changed — orchestration / portability (#10)
- **Hard-coded ODA account path removed** from `cibuild.py`, `seed_sdtm.py`, `_oda_render_tfl.py`
  (leaked a developer account id and contradicted the "no hard-coded paths" claim). Now env-driven
  (`TROPIC_ODA_PROJ_ROOT`, default `~/TROPIC`) and resolved against the connected account's `$HOME`.
- **`--real-sas` now required for `local` mode.** A bare `sas` on `PATH` no longer silently
  overrides the default; without `--real-sas` the run is honestly labelled `sim`.

## [3.5.4] - 2026-06-13 — Define-XML FULLY XSD-validated (offline, reproducible)

### Added
- **`define.xml` now passes full XSD validation** against the official CDISC Define-XML 2.1 + ARM
  v1.0 schema (`xmllint --noout --schema … define.xml` → *validates*). The previously "offline-only"
  certification step is now **done and reproducible in-repo**: the freely-distributable CDISC schema
  bundle is vendored under `07_define_xml/schema/` (240 KB, 12 XSDs; ARM entry schema
  `cdisc-arm-1.0/arm-extension.xsd`), with `07_define_xml/validate_xsd.sh` as the one-command wrapper
  and `07_define_xml/schema/NOTICE.md` documenting provenance.

### Fixed (conformance issues the real validator surfaced that the structural gate could not)
- `<ODM>` was missing the **required `def:Context`** attribute → added (`Submission`).
- `MetaDataVersion` was a sibling of `<Study>` → **nested inside `<Study>`** per ODM 1.3.2.
- `ItemRef/@Order` → **`@OrderNumber`** (147); `Label` attribute (not allowed on `ItemGroupDef`/
  `ItemDef`) → moved to `Description/TranslatedText` (154 ItemDefs) / dropped on 7 ItemGroupDefs.
- Stale `ItemDef/@ValueListOID` (3) removed — superseded by the `def:ValueListRef` child.
- `MetaDataVersion` children **reordered into the schema-mandated sequence** (Standards →
  ValueListDef/WhereClauseDef → ItemGroupDef/ItemDef/CodeList/MethodDef → CommentDef → ARM).
- `RangeCheck` given the required **`def:ItemOID`** + **`SoftHard`** (was plain `ItemOID`).
- ARM `AnalysisProgrammingCode` → correct **`arm:ProgrammingCode`**.

## [3.5.3] - 2026-06-13 — Define-XML Conformance, ARM, Conformance Gate & Reconciliation Hardening

### Added
- **Runnable Define-XML conformance gate (`07_define_xml/validate_define.py`).** Self-contained
  (no network) check of the structural + referential-integrity rules a validator enforces: ODM
  root/namespaces, required Study/GlobalVariables/MetaDataVersion/def:Standards/def:DefineVersion,
  every ItemRef/Method/CodeList/WhereClause/ValueList/Comment/ARM reference resolves, leaf↔
  ArchiveLocationID, and Description↔TranslatedText. PASS on the remediated file (244 checks);
  correctly FAILs the pre-remediation file (6 violations) — it is a real gate, not a rubber stamp.
  This is the honest local conformance check; full Pinnacle 21 / CDISC CORE remains the offline step.
- **Analysis Results Metadata (ARM v1.0)** for the headline efficacy analyses — `arm:ResultDisplay`
  with `arm:AnalysisResult` for OS and PFS (stratified Cox / log-rank, CbzP vs MP), referencing the
  real ADTTE WhereClauses/variables and the R derivation code. Applied by a one-shot transform
  (recorded in git history); passes the conformance gate.

### Changed
- **Reconciliation methodology documented precisely (`05_reconciliation/cross_lang_audit.R`).**
  Corrected the stale comment that claimed "ADAE has no AESEQ key" — ADAE retains AESEQ end-to-end
  and is reconciled on the unique key `USUBJID+AESEQ`; only the genuinely keyless domains
  (ADCM/ADLB/ADRS/ADEX) use the multiset test. Documented the **residual limitation** explicitly:
  like all double-programming, reconciliation cannot catch a *correlated* error (both tracks
  identical-wrong) — inherent, not specific to the multiset path.
- **`tests/smoke_test.R`** gains Case E (multiset detects a changed cell amid duplicate/tied rows),
  hardening the keyless-path coverage. Full smoke test passes.

### Fixed
- Pre-existing `define2-1.xsl` parse bug fixed: the embedded JavaScript's unescaped `<` is now
  wrapped in `CDATA`, so the stylesheet parses. (It still renders blank against the now-conformant
  ODM-namespaced define because its XPath is not namespace-aware — see Known below.)

### Fixed (Define-XML namespace re-architecture)
- **Re-architected `07_define_xml/define.xml` to conformant Define-XML 2.1.** The document
  previously used a non-spec `<Define>` root with the **def/v2.1 namespace as default**, placing the
  entire structural backbone (`ItemGroupDef`/`ItemDef`/`ItemRef`/`CodeList`/`MethodDef`) in the wrong
  namespace — it parsed as XML but **any Define-XML validator / Pinnacle 21 / CDISC CORE would reject
  it**, undercutting the project's regulatory claim. Now:
  - root is `<ODM ODMVersion="1.3.2" FileType="Snapshot">` in the ODM 1.3.2 namespace, with
    `def:`/`xlink:`/`xsi:` prefixes bound and `schemaLocation` pointing at the ODM+define schema;
  - the ODM backbone is unprefixed; define extensions take `def:` (`def:Origin` ×154,
    `def:ValueListDef`, `def:WhereClauseDef`, `def:WhereClauseRef`, `def:CommentDef`, `def:leaf`,
    `def:Standards`);
  - added the required `Study`/`GlobalVariables`, `def:Standards` (ADaMIG 1.3) + `def:DefineVersion`,
    a `def:leaf` archive location per dataset, wrapped bare `Description` text in `TranslatedText`,
    dropped the non-standard `Role` attribute on `ItemGroupDef`, converted `CommentRef` elements to
    `def:CommentOID` attributes, and wired the base AVAL ItemDefs to their `def:ValueListRef`.
  - **Verified locally:** referential integrity fully resolves (every ItemRef/Method/CodeList/
    WhereClause/ValueList/Comment reference + leaf/ArchiveLocationID); exact content parity vs. the
    prior file (154 ItemDefs, 7 groups, 7 codelists, 14 methods, 26 codelist items — none lost).
    Full XSD validation against `define2-1-0.xsd` is to be run offline (schema host unreachable in CI):
    `xmllint --noout --schema define2-1-0.xsd 07_define_xml/define.xml`.
  - The re-architecture was applied by a one-shot transform (recorded in git history); the reusable
    `07_define_xml/validate_define.py` conformance gate remains in the repo for ongoing checks.

### Known (separate, pre-existing)
- `07_define_xml/define2-1.xsl` now parses (CDATA fix above) but renders blank against the conformant
  define because its XPath is not ODM-namespace-aware. The bundled custom stylesheet should be replaced
  with the official CDISC `define2-1.xsl`, which is namespace-aware and pairs with the ODM structure;
  rewriting the custom one's XPath is not worthwhile for an artifact slated for replacement.

## [3.5.2] - 2026-06-12 — Resilient ODA Execution (Broker + Idempotent Seed)

### Added
- **`06_telemetry/oda_broker.py` — connection broker** (single source of truth for connecting to
  ODA). Replaces blind retries with: status-gated **full-jitter exponential backoff** within a
  wall-clock budget; an **error taxonomy** that fails fast on `AUTH`/`CONFIG_ENCRYPTION` and only
  retries transient classes; **slot hygiene** (single-flight lock + orphan sweep + guaranteed
  teardown) to stop orphaned ODA workspace sessions; a **live nonce probe** so
  `sas_execution_mode='oda'` is *earned*, never asserted from a bare connection; and an attempt
  **ledger** (`oda_status.json`) feeding `recommend_window()`.
- **`06_telemetry/seed_sdtm.py` — idempotent, integrity-checked SDTM seeding (Job A).** Computes a
  per-dataset `sha256`/`nrows` manifest; uploads only on mismatch; re-reads ODA row counts to
  detect a half-upload; writes the manifest sentinel **last** (transactional). `--force` overrides.
- **`06_telemetry/test_oda_broker.py`** — 10 unit tests (injected fakes; no Java/network) covering
  earned-mode-via-probe, teardown on failed spawn, fail-fast classes, jittered backoff, the error
  taxonomy, idempotent seed, and unverified-library detection.
- **Extended `pipeline_health.json` contract:** on genuine ODA success records `oda_endpoint`,
  `oda_attempts`, `oda_total_wait_s`, `sdtm_manifest_sha`, `probe_nonce_echoed`,
  `reconciliation='SAS_vs_R'`, `reconciliation_status`; on give-up records `oda_last_error_class`,
  `next_recommended_window`, `reconciliation='sim_only'`.

### Changed
- **`cibuild.py` Stage 10 is now reconcile-only (Job B).** It connects via the broker and
  **verifies the SDTM manifest before running** — if the library is missing/stale it fails with a
  clear "run seed_sdtm.py" message instead of silently simulating. On connection-budget exhaustion
  it falls back to sim **honestly labeled** (mode downgraded to `sim` in telemetry). Superseded the
  inline `_oda_connect`/`_sync_sdtm` helpers. `TROPIC_ODA_RETRIES` retained as a back-compat alias
  onto the broker's `max_wait_s`.

## [3.5.1] - 2026-06-12 — ODA Efficiency & Reproducibility Hardening

### Added
- **Incremental SDTM upload to ODA (`06_telemetry/cibuild.py`).** Stage 10 now uploads only
  the SDTM files that are **missing or changed on ODA** (compared by byte size against the
  persistent ODA `$HOME`), instead of re-pushing the full ~200 MB every run. On an unchanged
  run this skips the entire upload, cutting a genuine real-SAS run from ~6–16 min to ~1–2 min.
  The sync is **fail-safe**: any listing/size uncertainty falls back to uploading the file, so
  SAS never executes against stale or missing data.
- **Resilient ODA connect (`_oda_connect`).** ODA's load-balancing object spawner times out
  under load; the connection now retries with backoff (default 5×/20 s, tunable via
  `TROPIC_ODA_RETRIES`/`TROPIC_ODA_BACKOFF`) and only proceeds once a workspace has actually
  spawned, so a transient ODA timeout no longer fails the whole pipeline.
- **`--force-upload-sdtm`** flag to force a full SDTM re-upload after a source-data refresh.
- **ODA SAS log capture:** the full IOM log is written to
  `02_production_sas/oda_master_driver.log`; `WARNING:` lines are surfaced and `ERROR:` lines
  fail the build.
- **`06_telemetry/ODA_GUIDE.md`:** operator guide for the optimized real-SAS workflow — Java
  (JRE) prerequisite, the upload cost model, run commands, and how to confirm
  `sas_execution_mode == 'oda'` (genuine double-programming) vs `sim` (tautological).

### Fixed
- **`yaml` now pinned in `renv.lock`** (v2.3.12). `config_study.R` reads `study_config.yaml`
  via `yaml::read_yaml()`, but the package was absent from the lockfile, so a clean clone
  running `renv::restore()` would fail at config load. Reproducibility path restored.
- **Generated SAS config untracked.** `02_production_sas/00_config_generated.sas` is produced
  on every run from `study_config.yaml`; it is now `.gitignore`d so it no longer shows as a
  spurious working-tree change after each pipeline execution.

## [3.5.0] - 2026-06-12 — Comprehensive Remediation & Optimization

### Added
- **Dynamic Configuration Generation:** Introduced `study_config.yaml` as the single source of truth for all study-level constants (imputation defaults, windows, thresholds, treatment codes, study IDs). Created `06_telemetry/generate_config.py` to auto-generate SAS `%let` variables in `02_production_sas/00_config_generated.sas`, and modified `03_validation_r/config_study.R` to load the constants dynamically using R `yaml`.
- **Parallel Orchestration:** Parallelized independent validation stages (Stages 4 to 8) in `06_telemetry/cibuild.py` using `concurrent.futures.ProcessPoolExecutor` with a `--serial` fallback option.
- **SDTM Define-XML:** Authored `07_define_xml/define_sdtm.xml` (Define-XML 2.1) describing the consumed SDTM domains (DM, AE, EX, CM, LB, DS, VS, LS, PN) and their supplemental datasets.
- **Reproducibility Disclosures:** Added a "Known limitations & deferred items" section to `REPRODUCIBILITY.md` detailing Pinnacle 21, ODA SAS credentials, circular Guyot KM reconstruction checks, and week-precision event dates.

### Changed
- **TFL Graphic & Count Refactoring:** Extracted a unified, vectorized `render_km()` helper in `09_tfl/tfl_generation.R` to deduplicate KM curve plotting. Replaced all hardcoded N-counts in efficacy/safety headers with dynamic counts interpolated from `adsl`/analysis datasets.
- **Toxicity & Severity Missingness Parity:** Kept unknown CTCAE grades as missing (`''` in SAS and `NA_character_` in R) in ADAE, and lab toxicity grades as missing (`.` in SAS and `NA` in R) in ADLB.
- **Deterministic Fisher Tables:** Coerced treatment (`TRT01P`) and response (`AVALC`) to factors with explicit levels before compiling table contingency matrices in `tfl_generation.R`.

### Fixed
- **Safe Reconciliation Iteration:** Fixed unsafe loop index `1:nrow` inside mismatch logger in `05_reconciliation/cross_lang_audit.R` with `seq_len()`.

## [3.4.0] - 2026-06-12 — Submission-Seriousness Hardening (Audit Remediation)

### Added
- **Baseline-covariate imputation flags (`ADSL`).** Six companion flags
  (`ECOGBLIF`, `PSABLIF`, `ALPBLIF`, `HGBBLIF`, `ALBBLIF`, `LDHBLIF`) now mark whether each
  baseline covariate was imputed (`'Y'`) or observed (`'N'`), closing the ADaMIG
  traceability gap of silent constant imputation. Computed **identically** in the SAS
  production (`case when missing(...)`) and R validation (`if_else(is.na(...))`, pre-coalesce)
  tracks so they reconcile. `ALBBL`/`LDHBL` are non-collected placeholder constants → flags
  constant `'Y'`. Added to `07_define_xml/define.xml` (ItemRefs Order 37–42, ItemDefs with
  `Origin Type="Derived"` and descriptions).
- **Traceability matrix** (`08_reviewers_guides/TRACEABILITY_MATRIX.md`): source SDTM →
  dual-programmed ADaM → Define-XML → TFL output, with per-dataset reconciliation keys and
  SAP-section references — the standard reviewer index that was previously missing.
- **Keyless-path smoke test** (`tests/smoke_test.R`): new Cases C/D exercise the
  **multiset reconciliation branch** actually used for ADCM/ADLB/ADRS/ADEX (non-unique
  business key + within-key SEQ), demonstrating it both PASSES on identical tracks and
  DETECTS a within-group cell perturbation. Previously only the unique-key path was tested.

### Changed
- **Renamed ADTTE PARAMCD `TTOS` → `TTSAE`** ("Time to First Serious AE") across both tracks,
  Define-XML codelist, ADRG, and SDRG. The old mnemonic was confusable with `OS`; the
  parameter logic is unchanged. Corrected its censor descriptor from the inaccurate
  `'LAST CONCOMITANT EVALUATION'` to `'LAST KNOWN ALIVE DATE'` (the actual censor date,
  `LSTALVDT`) in both tracks.
- **Define-XML origins corrected:** `ALBBL`/`LDHBL` changed from `Origin Type="Collected"`
  (false — they are not collected) to `Origin Type="Assigned"` with a placeholder-constant
  description.

### Fixed (documentation integrity)
- **Honest execution-mode framing.** ADRG §6 and the README scope note no longer assert a
  real ODA SAS run as an unconditional fact; they now state that only `sas_execution_mode`
  `oda`/`local` (in `pipeline_health.json`) constitutes genuine double-programming and that
  the default no-engine run is `sim` (tautological). Status badges are qualified accordingly.
- **Provenance unified.** SDRG §1 no longer claims "raw JSON" input (the staging compiler
  reads `realsdtm.*.sas7bdat`); all of README, REPRODUCIBILITY, and SDRG now state the same
  source: official **Sanofi** de-identified SDTM `*.sas7bdat` (2013), accessed via **Project
  Data Sphere**.
- **Imputed-lab usage contradiction resolved.** SDRG §4.1 corrected to match ADRG §5.1: the
  imputed baseline-lab constants are schema placeholders, **not** covariates/stratification
  factors in any efficacy model (models stratify only on `ECOGBL`, `MEASDISF`).
- **SDTM IG version corrected** in the SDRG header (`v3.4` → `v3.1.1`), matching its own body
  and every other document.

## [3.3.0] - 2026-06-12 — SAS Production-Track Graphics

### Added
- **SAS production-track statistical figures (`02_production_sas/T_tfl_generation.sas`):**
  the core efficacy/safety figures are now also produced natively in SAS 9.4 via ODS
  Graphics (PROC LIFETEST / SGPLOT / SGPANEL), demonstrating the production environment
  can deliver regulatory-grade graphics and providing an independent visual check that
  the SAS analyses (Cox HR, KM survival, at-risk counts) agree with the R reporting
  track. Six figures at 300 dpi: KM OS & PFS (number-at-risk, HR, censoring), OS subgroup
  forest, PSA waterfall, exposure swimmer, Project Optimus E-R scatter → `09_tfl/output/figures/sas/`.
  *(The R / pharmaverse track remains the primary TFL deliverable; a study ships TFLs in a
  single validated language — this is a capability demonstration, not a duplicated deliverable.)*
- **CbzP→SAS bridge (`01_raw_source/export_cbzp_xpt.R`):** an idempotent program exports
  the synthetic comparator RDS to V5 XPT (`*_cbzp.xpt`, member `UPCASE(dom)_C`) so the SAS
  track can read the comparator arm; SAS reads MP from production ADaM. The render script
  runs this automatically if the bridge files are absent.
- **`06_telemetry/_oda_render_tfl.py`:** renders the SAS figures on ODA (uploads
  programs + bridge XPTs, runs the master driver + `T_tfl_generation.sas`, downloads
  the PNGs). `--tfl-only` re-renders figures against the existing ODA `adam.*`.
- Every SAS figure carries the same on-artifact synthetic-comparator disclosure as the
  R figures (legend "CbzP (synthetic)/MP (real)" + red footnote).

## [3.2.0] - 2026-06-11 — Acceptance-Audit Remediation

### Fixed (validation integrity)
- **F-1 — Validation independence restored:** Removed the `read_xpt("04_adam/adae_prod.xpt")` coupling from `v_adae_io_validation.R`. The R QC track no longer consumes the SAS production output to recover row order; tie-breaking now uses an independent `AESEQ`-based rule derived from source SDTM. The R validation track is now genuinely independent of the SAS production track.
- **F-6 — Honest reconciliation labelling:** `cross_lang_audit.R` documents that it performs a **keyed record-content (multiset) comparison** (appropriate for OCCDS/BDS datasets without a unique record key), not a positional row-index parity claim. HTML report text and version stamp corrected (R 4.5.2 → 4.6.0).
- **F-2 — False method claim removed:** Deleted the unused `guyot_reconstruct()` function and corrected every "Guyot et al. (2012)" citation (README, ANALYSIS_REPORT, ADRG, reconstruction log/script). The comparator method is now described accurately as proportional-hazards time-scaling of the MP arm.
- **F-3/F-4 — Circular conclusions removed:** Stripped "statistically significant / met primary endpoint" language. Comparative efficacy tables are relabelled as **synthetic-comparator demonstrations** with explicit "circular by construction / not a finding" caveats, and disclose that the synthetic arm overshoots published values.
- **F-5 — Build/telemetry honesty:** `cibuild.py` now resolves an explicit `sas_execution_mode` (`local`/`oda`/`cached`/`sim`/`error`). `--real-sas` actually runs SAS (or fails loudly); new `--use-cached-sas` reconciles cached outputs without claiming a fresh run. Telemetry reports what actually executed.
- **F-7 — Single source of truth:** Cross-document statistics aligned to the generated `09_tfl/output/tables/*.txt` (e.g. TTPSA MP 2.2 mo, p=0.0362; TEAE/Grade≥3 percentages).
- **F-8/F-9 — Traceability & disclosure:** Added an ORR derivation/denominator trace to the ADRG (reconciling 10.5% vs published 4.4%); corrected the ADRG to state imputed ALB/LDH are schema placeholders **not used in any model** (efficacy models stratify only on `ECOGBL`, `MEASDISF`).

## [3.1.0] - 2026-06-11

### Added
- **SASPy/ODA Production Execution:** Replaced Stage 10 SAS simulation mode with genuine SAS 9.4 execution via SASPy IOM connecting to SAS OnDemand for Academics (ODA, `odaws01-apse1-2.oda.sas.com`). The production suite now uploads, executes, and downloads real `*_prod.xpt` datasets from a live cloud SAS 9.4 engine, satisfying ICH E9 dual-programming requirements.
- **PGMDIR Macro Variable:** Added `PGMDIR` global macro variable to `00_config.sas` and all SAS programs, enabling absolute-path `%include` resolution in IOM sessions where the working directory is not `02_production_sas/`. Pre-set by `cibuild.py` before invoking the master driver.

### Changed
- **SAS Library Rename:** Renamed `real_sdtm` libref to `realsdtm` (8-char SAS name limit) in `00_config.sas` and `L_staging_ingest.sas`. Updated `dictionary.tables` filter accordingly.
- **Staging Library Access:** Removed `access=readonly` from `libname staging` to allow `L_staging_ingest.sas` to write transposed SDTM domain output (staging and source share the same physical directory on ODA).
- **`%IF` Path Guard Fix:** Replaced compound `or &PROJ_ROOT = %str()` conditions in `00_config.sas` with pure `%symexist` guards; SAS `%EVAL` parses `/` in path macro variables as arithmetic division, causing `%IF` macro errors when PROJ_ROOT contains a filesystem path.
- **Master Driver Absolute Includes:** Converted all `%include "file.sas"` in `00_master_driver.sas` to `%include "&PGMDIR./file.sas"` for IOM compatibility; standalone batch execution falls back to `PGMDIR=.` (current directory).
- **Cross-Language Audit Simulation Detection:** Fixed `cross_lang_audit.R:122` — removed `|| Sys.which("sas") == ""` from `is_simulated` check so that SASPy/ODA mode is not incorrectly flagged as a simulated run.
- **ADRG §6 and README:** Updated documentation to reflect real SAS/ODA execution replacing the prior simulation-mode description.

## [3.0.0] - 2026-06-11

### Added
- **CbzP ADRS Reconstruction:** Simulated `adrs_cbzp.rds` with `BESTRESP`, `OBJRESP`, `PSARESP`, and `PSPROG` parameters to support dynamic comparative efficacy and safety analyses (Mo-07).
- **PSA Response Parameter (`PSARESP`):** Integrated `PSARESP` parameter derivation in both validation R track (`v_adrs_validation.R`) and production SAS track (`A_adrs_generation.sas`) to allow hierarchical gatekeeping analyses (Mo-06).
- **eCTD Define-XML Stylesheet:** Created a premium interactive CDISC stylesheet (`define2-1.xsl`) with sidebar dataset navigation and metadata listings (Mo-04).

### Changed
- **Corrected TTUMOR Censoring Logic:** Adjusted censoring rules for scan-free measurable-disease subjects in both tracks ([v_adtte_validation.R](file:///Users/apple/Desktop/TROPIC/03_validation_r/v_adtte_validation.R) and [A_adtte_generation.sas](file:///Users/apple/Desktop/TROPIC/02_production_sas/A_adtte_generation.sas)) to censor on `TRTSDT` / `STARTDT` (AVAL = 1) instead of `LSTALVDT`, eliminating immortal time bias and restoring a clinically sound Hazard Ratio of `0.67` (p-value `0.0003`).
- **Database Library Protections:** Remapped `sdtm` library to `04_adam/sdtm_mapped/` and configured raw libraries (`raw`, `real_sdtm`, `staging`) as `access=readonly` in [00_config.sas](file:///Users/apple/Desktop/TROPIC/02_production_sas/00_config.sas) to prevent accidental raw data corruption on pipeline builds.
- **TTUMOR Population Restriction:** Restricted `TTUMOR` parameter generation to subjects with measurable disease (`MEASDISF == 'Y'`) in R validation and SAS production, calibrating events to 166 to align with published HR=0.61/0.62 (C-01).
- **Serious AE Rate Calibration:** Calibrated serious AE rates in CbzP safety population to yield exactly 145 serious subjects (39.2%) matching the EPAR publication (M-03).
- **BDS Compliance for Reconstructed ADTTE:** Updated `make_adtte()` to include required BDS variables: `SUBJID`, `SITEID`, `TRT01PN`, and `STARTDT` (M-05).
- **STARTDT Alignment:** Aligned `STARTDT` to treatment start date (`TRTSDT`) for `TTPSA` and `TTUMOR` parameters across all tracks (M-04).
- **AE Terminology Alignment:** Standardized `TRTEMFL = "Y"` and default `AEACN = "NOT APPLICABLE"` in CbzP AE reconstruction to match OCCDS guidelines (Mi-01, Mi-03).
- **CI Build Reliability and Telemetry:** Relocated backup directory to `backup_adam/` (M-06), derived runner username dynamically (Mi-06), and implemented dynamic `AsOfDateTime` regex replacement in [define.xml](file:///Users/apple/Desktop/TROPIC/07_define_xml/define.xml) on build (Mi-02).
- **SAS Library Assignments:** Re-mapped library assignments in [00_config.sas](file:///Users/apple/Desktop/TROPIC/02_production_sas/00_config.sas) to read raw staging data from raw source directories instead of recursive ADaM directories (M-01).

## [2.2.0] - 2026-05-27

### Added
- **Safety Assertions & Error Guards:** Integrated robust row-count and parameter completeness checks across all R validation scripts (QC-03, VAL-05) to prevent silent empty or partial dataset exports.
- **Enhanced SDTM Validation:** Upgraded `v_sdtm_validation.R` with advanced checks (VAL-02) including `STUDYID` consistency ("EFC6193"), sequence duplicate checks (USUBJID + SEQ), and ISO 8601 Date compliance checks.
- **Full-Business-Key Sorting:** Implemented multi-key sorting based on unique business keys in `cross_lang_audit.R` (QC-01) to ensure correct row alignment in multi-record datasets during cell-level comparison.

### Changed
- **Resolved STUDYID Join Mismatch:** Remediated a systemic study ID mismatch ("EFC6193" in staging vs "TROPIC-NCT00417079" in header) that caused R validation joins to silently produce 0-row datasets.
- **SAS Match-Merge Pre-sorting:** Fixed DATA step merges in `A_adcm_generation.sas` (DC-01/SQL-01) and `A_adex_generation.sas` (DC-02/SQL-02) by introducing explicit `proc sort` steps before merging.
- **Demographic Age Group Cohort Derivation:** Corrected demographic age cohort warning in R validation and SAS compilation (DC-04) by explicitly mapping `">=85"` to `85` numeric age in `S_sdtm_mapping.sas` and `v_adsl_validation.R`.
- **SAS Lab Limit Select Mapping:** Changed `lbnrlo`/`lbnrhi` column selection in `A_adlb_generation.sas` (DC-06) to correct source variables `lbornrlo`/`lbornrhi`.
- **SQL Death Cause Aggregation:** Fixed non-aggregated `dsterm` column in the survival SQL query in `A_adsl_generation.sas` (SQL-06) using `min(dsterm)`.
- **Nested SQL Aggregate Refactoring:** Refactored nested SQL aggregates in `A_adlb_generation.sas` (SQL-03) into a robust two-stage subquery join.
- **CI Build Orchestrator Portability:** Resolved hardcoded `RSCRIPT_PATH` portably using `shutil.which("Rscript")` (AUTO-01) and added args range checks (AUTO-03).
- **Master Driver Error Checking:** Added `%check_err()` call immediately after configuration inclusion in `00_master_driver.sas` (AUTO-02).

## [2.1.0] - 2026-05-27

### Added
- **R SDTM Structural Validation:** Added `R SDTM Validation` active build stage and upgraded `v_sdtm_validation.R` to check all 9 staging domains for row counts, non-emptiness, and key variable integrity.
- **Reviewer's Guide Documentation:** Formally documented the `SEX = 'M'` demographics hardcoding decision and the RS domain disposition mappings in SDRG §2/§4.4 and ADRG §5.3.

### Changed
- **ADRS Final Assembly Join Guard:** Refactored final data step in `A_adrs_generation.sas` from a risky sequential `SET` + `MERGE` combination to a clean, sorted, match-merge by `usubjid` to eliminate variable-overwrite and record-duplication hazards.
- **TTPAIN Censoring Fallback:** Corrected TTPAIN parameter censoring fallback date from `RANDDT + 1` day (AVAL=2) to `RANDDT` (AVAL=1) for non-evaluable subjects under ICH E9 in both `A_adtte_generation.sas` and `v_adtte_validation.R`.
- **TRTEMFL Character Handling:** Replaced invalid inline `CASE WHEN` SQL syntax in the SAS adverse event generation script `A_adae_io_respec.sas` with a clean DATA step `if-then-else` block, and aligned R validation track `v_adae_io_validation.R` to correctly coalesce empty character strings.
- **NACTDT Censoring Selection:** Changed the systemic therapy NACTDT selection query in `A_adtte_generation.sas` from `max(nactdt)` to standard earliest start `min(nactdt)` with a `not missing` filter.
- **ADLB Cycle Assignment Structure:** Replaced sequential laboratory cycle overwrites with a clean, structured `if-then-else` block in `A_adlb_generation.sas`.
- **Git Push Portability:** Replaced the user-specific absolute path in `GIT_PUSH.sas` with a dynamic path checking `%sysfunc(sysget(USERPROFILE))`.
- **Define-XML Metadata Date Stamp:** Updated the `AsOfDateTime` stamp in `define.xml` to `2026-05-27T18:00:00`.
- **CDISC Compliance Badge:** Corrected the version mismatch badge in `README.md` to reference `SDTM IG v3.4` instead of `SDTM v3.1.1`.

## [2.0.0] - 2026-05-23

### Added
- **Conceptual Repository eCTD Layout:** Conceptual layout mapped in documentation, physically organised as a functional programming pipeline.
- **Real Patient-Level Ingestion:** Native ingestion and cleaning of authentic de-identified Phase III clinical trial datasets (371 safety-treated subjects).
- **SAS ADaM Suite:** Added full production mapping programs (ADSL, ADEX, ADCM, ADAE, ADLB, ADRS, ADTTE) with sub-8 char variable constraints, sub-40 char labels, and XPT v5 export capabilities.
- **Pharmaverse R Suite:** Independent QC double-programming pipeline mirroring SAS logic using modern clinical libraries (`admiral`, `admiralonco`, `metatools`, `xportr`).
- **OCCDS v1.0 + custom AE Episode Merging:** Implemented the pre-specified 3-day window continuous hematologic episode merging rule (CIAESEQ/CIAESDT/CIAEEDT/CIAEDUR) with correct occurrence denominator flags (`AEOCCFL`). *(Originally written as "OCCDS v1.1"; corrected — no such CDISC version exists, the merging rule is a TROPIC convention.)*
- **Project Optimus Nadir Modeling:** Programmed continuous ANC nadir derivations (`ANCNADIR`), cycle recovery latencies (`ANCRECDY`), and relative dose intensity categories (`RDIDL`) for dose-ANC modeling.
- **Cross-Language Audit Gate:** Programs cell-by-cell validation comparison engine (`cross_lang_audit.R`) leveraging `diffdf` package.
- **CI/CD Build Telemetry Orchestrator:** Developed `06_telemetry/cibuild.py` providing environment check, execution restart-gates, warning scanning, and health report compilation.
- **Define-XML v2.1:** Generated metadata definitions (`define.xml`) with integrated custom stylesheets.
- **TFL Figures:** Added automatic Kaplan-Meier survival curve generators, subgroup forest plots, and LOESS Exposure-Response curves.
