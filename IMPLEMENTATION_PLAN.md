# TROPIC Pipeline — Comprehensive Remediation & Optimization Implementation Plan

You are a Principal Clinical Programmer + R/SAS engineer working in the repo at
`/Users/apple/Desktop/TROPIC`. This is a dual-language (SAS production + R validation)
CDISC ADaM pipeline for the TROPIC mCRPC trial (real Mitoxantrone arm N=371 + a SYNTHETIC,
illustrative Cabazitaxel comparator). Execute the plan below in phases, verifying after each.

## 0. NON-NEGOTIABLE INVARIANTS (read first — violating these breaks the pipeline)

1. **Dual-track symmetry.** Every ADaM dataset is produced TWICE: SAS production
   (`02_production_sas/A_*.sas` → `*_prod.xpt`) and R validation
   (`03_validation_r/v_*.R` → `*_v.xpt`). They are reconciled cell-by-cell by
   `05_reconciliation/cross_lang_audit.R` (diffdf). **Any change to a derivation, column,
   value, or name MUST be made identically in BOTH tracks AND in `07_define_xml/define.xml`,**
   or reconciliation fails. When you change one track, change the other in the same commit.
2. **Honesty over polish.** This is a portfolio/demo with a SYNTHETIC comparator and (by
   default) no real SAS run. NEVER fabricate evidence: do not invent Pinnacle 21 reports,
   do not claim a real SAS/ODA run occurred, do not commit fake "submission-ready" badges.
   Where something can't truly be produced, DOCUMENT the limitation honestly instead.
3. **Tooling reality.** `Rscript` (R 4.6.0) IS available — use it to parse-check and run R.
   There is **NO SAS engine and NO source data locally**, so SAS edits are
   syntax-only-verified; state that in your summary. `python3` is available.
4. **Do not push.** Work on a new branch off `main`. Commit logically. Do NOT push or open a
   PR unless explicitly told.
5. **Verify continuously.** After each phase: `Rscript -e "parse('<file>')"` on changed R,
   `python3 06_telemetry/cibuild.py --demo` (runs `tests/smoke_test.R`), and
   `python3 -c "import xml.dom.minidom as m; m.parse('07_define_xml/define.xml')"` after any
   define.xml edit.

## ALREADY DONE (do NOT redo — verify they're intact)
- Three doc contradictions fixed: provenance unified (Sanofi SDTM `*.sas7bdat` via Project
  Data Sphere; the "raw JSON" claim removed), imputed-lab model-use (SDRG §4.1 == ADRG §5.1),
  SDTM version (SDRG header v3.1.1).
- ADSL imputation flags `ECOGBLIF/PSABLIF/ALPBLIF/HGBBLIF/ALBBLIF/LDHBLIF` added to SAS + R +
  define.xml (computed identically; pre-coalesce in R).
- `TTOS` PARAMCD renamed to `TTSAE` everywhere; its censor descriptor fixed to
  `LAST KNOWN ALIVE DATE`.
- Sim-mode honesty added to ADRG §6 and README; `ALBBL`/`LDHBL` define origin → `Assigned`.
- `08_reviewers_guides/TRACEABILITY_MATRIX.md` added; `tests/smoke_test.R` hardened with a
  keyless-multiset path test (Cases C/D).
These may exist as uncommitted working-tree changes or already-committed work. Start from the
current repo state; do not undo them.

---

## PHASE 1 — Remaining data-integrity / correctness (symmetric SAS+R)

**1.1 Stop coercing missing CTCAE severity to MILD.**
- `02_production_sas/A_adae_io_respec.sas`: the `AESEV` CASE maps grade 1→MILD, 2→MODERATE,
  ≥3→SEVERE, `else 'MILD'`. Change the `else` to missing (`''`), so an unknown grade is not
  reported as MILD.
- `03_validation_r/v_adae_io_validation.R`: the matching `AESEV = case_when(... TRUE ~ "MILD")`
  → `TRUE ~ NA_character_`. Must match SAS exactly.
- Confirm no TFL or downstream code assumes AESEV is always non-missing; if it does, handle NA.

**1.2 Stop coercing missing lab tox grade to 0 (normal) in ADLB.**
- `02_production_sas/A_adlb_generation.sas` line ~55: `coalesce(input(lb.lbtoxgr,best32.),0.0) as ATOXGR`
  defaults missing grade to 0. Change so missing stays missing (`.`), and verify the
  `ANL01FL` worst-grade sort (`descending ATOXGR`) and the baseline/worst shift logic treat
  missing as "exclude," not "Grade 0."
- Mirror the identical change in `03_validation_r/v_adlb_validation.R`.
- ⚠️ This changes analytic output (shift tables, ANL01FL). Re-run the R validation logic if
  you can; document that the SAS side is unverified locally. If the risk is unacceptable
  without data to test against, instead ADD an explicit `ATOXGRFL`/comment documenting the
  imputation rather than changing the value — your call, but justify it.

**1.3 Robustness: deterministic Fisher tables.**
- `09_tfl/tfl_generation.R` lines ~101-102 and ~112-113: before `table(...)`, coerce
  `TRT01P <- factor(TRT01P, levels=c("MP","CbzP"))` and `AVALC <- factor(AVALC, levels=c("N","Y"))`
  so the contingency table is always a clean 2×2 regardless of stray levels.

---

## PHASE 2 — TFL refactor (R-only, fully verifiable locally)

Goal: remove duplication and redundant computation in `09_tfl/tfl_generation.R` WITHOUT
changing any output number or pixel. After refactor, regenerate and confirm the output
`.txt` tables are numerically identical and the PNGs still render.

**2.1 Extract a single `render_km()` helper.** The OS block (lines ~152-250) and PFS block
(lines ~676-750) are near-identical: `survfit` → step-extraction → number-at-risk →
main ggplot → risk-table ggplot → `patchwork` stack → `ggsave`. Factor into one function
`render_km(data, stats, x_max, x_by, title, subtitle_endpoint, y_lab, outfile)` and call it
for OS (x_max=24) and PFS (x_max=18). Keep colors/labels/theme identical.

**2.2 Fit each KM once.** Within `render_km`, call `survfit(Surv(AVAL/30.4375, 1-CNSR) ~ TRT01P)`
ONCE and derive BOTH the step data and the number-at-risk from it (use
`summary(fit, times=seq(0,x_max,x_by))$n.risk` / `$strata`). Remove the per-arm
`survfit(~1)` refits at lines ~217 and ~724. (`compute_tte_stats()` keeps its own coxph/survdiff.)

**2.3 Vectorize the risk table — remove `rbind`-in-loop.** Replace the `for` loops at
lines ~214-225 and ~721-732 (`risk_data <- rbind(risk_data, ...)`) with a vectorized build
(`expand.grid(TRT01P, Time)` + `summary(fit, times=)` lookup, or `purrr::map_dfr`).

**2.4 Precompute AE summary counts once.** Lines ~933-946 recompute the same
`filter |> distinct |> nrow` per-arm counts repeatedly inside one `sprintf`. Build one small
summary frame (`group_by(TRT01P) |> summarise(any_teae=n_distinct(USUBJID), g3=…, sae=…)`)
and index into it for both numerator and percentage so they can't drift.

**2.5 Derive hardcoded population counts.** Replace literal `N=378`/`N=371`/`N=179`/`N=203`
in the table header strings (lines ~599, ~609, ~628) and the `else 378` fallback (line ~871)
with values computed from `adsl`/the analysis frames, interpolated via `sprintf`.

**Verify Phase 2:** `Rscript 09_tfl/tfl_generation.R` must run clean and reproduce the same
numbers in `09_tfl/output/*.txt`. Diff the regenerated tables against the originals (git diff)
— numeric content should be unchanged; only formatting from derived-N may differ.

---

## PHASE 3 — Reconciliation engine

**3.1 Fix unsafe loop index.** `05_reconciliation/cross_lang_audit.R` line ~125:
`for (i in 1:nrow(num_diff))` → `for (i in seq_len(nrow(num_diff)))`.
**3.2 (Optional perf, only if you can keep semantics identical):** the all-column
`arrange(across(...))` on ~79k-row ADLB is the heaviest op. You MAY replace the N-column sort
with a single composite key (`tidyr::unite` of the content columns into one string, sort on
that) IF and only if it produces identical pairing. Add a smoke-test case proving equivalence
before adopting. If unsure, leave as-is.

---

## PHASE 4 — Orchestration (`06_telemetry/cibuild.py`)

**4.1 Parallelize the independent R ADaM validations.** The dependency DAG is:
`staging → ADSL → {ADEX, ADCM, ADAE, ADLB, ADRS} → ADTTE → reconcile → TFL`. Stages 4-8
(ADEX/ADCM/ADAE/ADLB/ADRS) only read `adsl_v.xpt` + staging and write their own `_v.xpt`, so
they are mutually independent and can run concurrently after ADSL. Use
`concurrent.futures.ProcessPoolExecutor` to fan them out, then run ADTTE, then reconcile.
Preserve: per-stage logrx logging, the existing fail-fast + auto-rollback behavior, the
`sas_execution_mode` resolution, and telemetry. Keep a `--serial` flag to fall back.
**4.2 (Optional) Incremental builds.** Add a simple mtime guard (skip a stage whose inputs are
older than its output) or note `targets`-package migration as a documented follow-up. Don't
half-build a caching system — either do it cleanly or leave a TODO.

**Verify Phase 4:** `python3 06_telemetry/cibuild.py --demo` still passes; `--dry-run` works.

---

## PHASE 5 — Single-source config (removes SAS/R drift risk)

Create `study_config.yaml` holding every study constant currently duplicated in
`02_production_sas/00_config.sas` and `03_validation_r/config_study.R` (thresholds, analysis
windows, imputation defaults, treatment codes, cutoff date). Then:
- R: `config_study.R` reads it via `yaml::read_yaml()` and assigns the same variable names.
- SAS: generate the `%let` statements from the YAML (a tiny R or Python pre-step that writes a
  `00_config_generated.sas`, or use `libname JSON`/`PROC LUA`). `00_config.sas` includes the
  generated file.
Keep variable names/values byte-identical to today so nothing else changes. Add `yaml` to
`renv.lock` if needed. Verify both tracks still produce the same constants.

---

## PHASE 6 — Larger submission artifacts (author truthfully; do NOT fabricate)

**6.1 SDTM define.xml.** Author `07_define_xml/define_sdtm.xml` (Define-XML 2.1) describing the
consumed SDTM domains (DM, EX, DS, VS, LB, LS, PN, CM, AE + SUPP--) at SDTMIG v3.1.1, mirroring
the structure/quality of the existing ADaM define. Add its stylesheet reference. This is
genuinely missing and is authorable from the known domain shapes.
**6.2 (Optional) Analysis Results Metadata (ARM)** in the ADaM define linking key TFL outputs
to their ADaM inputs + methods. Only if time allows; keep it accurate.
**6.3 Explicitly DEFERRED — document, do not fake** (add/keep a short "Known limitations &
deferred items" section in `REPRODUCIBILITY.md`):
   - **Pinnacle 21 conformance report** — requires the P21 tool + data; cannot be generated
     here. State that running P21 is a required pre-submission step.
   - **Real ODA SAS run evidence** — requires ODA credentials + data; the default run is `sim`.
   - **Guyot (2012) KM reconstruction of CbzP** — a DESIGN CHOICE, not required for credibility
     (the synthetic arm is honestly labeled). Note it as the recommended upgrade IF a two-arm
     comparison is retained; current divide-by-HR method is documented as circular.
   - **Week-precision event dates** (±3.5 d) — inherent to the source; already disclosed.

---

## PHASE 7 — Finalize

1. Run the full verification suite: parse-check ALL changed R; `python3 06_telemetry/cibuild.py
   --demo` PASSES; define.xml(s) well-formed; `Rscript 09_tfl/tfl_generation.R` reproduces
   outputs.
2. Update `CHANGELOG.md` with a new version entry summarizing every change, grouped
   Added/Changed/Fixed, honest about verification status (R verified; SAS syntax-only).
3. Bump the `Version:`/`Date:` header of every program you modified.
4. Commit on a branch (e.g., `remediation/v3.5.0`) with clear messages. Do NOT push.
5. In your final summary, state explicitly: what was changed, what was verified vs.
   SAS-unverified (no engine/data locally), and what was deliberately deferred (Phase 6.3) and
   why. Do not claim submission-readiness — claim "as rigorous as achievable without real
   data, a real SAS run, and Pinnacle 21."

## Acceptance criteria
- `python3 06_telemetry/cibuild.py --demo` → SMOKE TEST: PASS.
- All changed R parses; `tfl_generation.R` runs clean and outputs are numerically unchanged
  (except intentionally derived-N headers).
- Every SAS derivation change has an identical R counterpart and matching define.xml metadata.
- No fabricated P21/SAS-run/Guyot artifacts. Limitations documented, not hidden.
- New branch, committed, not pushed.
