# admiral Re-derivation Track — ADSL + ADTTE (Finding #4)

A **third, independent derivation track** for TROPIC built with the pharmaverse
[`admiral`](https://pharmaverse.github.io/admiral/) package (v1.5.0) — the
industry-standard, validated ADaM toolkit — reconciled cell-for-cell against the
SAS production track. This complements the existing SAS production
(`02_production_sas/`) and hand-rolled R validation (`03_validation_r/v_*`) tracks.

## Why

The portfolio's moat is reconciliation-as-code. Adding an admiral track demonstrates
fluency in the modern pharmaverse standard *and* extends the reconciliation framework
to a third engine: where the bespoke SAS and R tracks could share a correlated error,
an independent admiral derivation using validated library functions is a stronger
check, and shows the derivations agree with the community-maintained reference
implementation.

## Components

| File | Role |
|---|---|
| `03_validation_r/admiral_adsl.R` | admiral ADSL core (`derive_vars_merged`, `derive_var_trtdurd`) → `04_adam/adsl_admiral.xpt` |
| `03_validation_r/admiral_adtte.R` | admiral ADTTE OS + PFS (`derive_param_tte`, `event_source`/`censor_source`) → `04_adam/adtte_admiral.xpt` |
| `05_reconciliation/admiral_reconcile.R` | scoped, exact (0-tolerance) diff vs `*_prod.xpt` → `06_telemetry/admiral_reconciliation_status.json` |

Run order:
```bash
Rscript 03_validation_r/admiral_adsl.R
Rscript 03_validation_r/admiral_adtte.R
Rscript 05_reconciliation/admiral_reconcile.R
```

## Result — exact agreement on the scoped core

| Domain | n | Cell diffs | Status |
|---|---|---|---|
| ADSL (16 core vars) | 371 | 0 | **PASS** |
| ADTTE · OS | 371 | 0 | **PASS** |
| ADTTE · PFS | 371 | 0 | **PASS** |

ADSL core = TRT01P/TRT01PN, RANDDT, TRTSDT, TRTEDT, TRTDURD, AGE, AGEGR1/N, SEX,
ITTFL, SAFFL, DTHFL, DTHDT, LSTALVDT.
ADTTE core = STARTDT, ADT, AVAL, CNSR, EVNTDESC, CNSDTDSC.

## Scope (honest)

- **Column-scoped.** admiral re-derives the admiral-idiomatic *core*. The
  study-specific ADSL baseline covariates (PSABL/ECOGBL/PAINBL/… and their `*IF`
  imputation flags) and the SAFETY ADTTE parameters (TTSAE/TTPAIN/TTPSA/TTUMOR) are
  **not** admiral-native and stay covered by the SAS+R double-programming.
- **MP arm only.** The ADaM ADTTE is MP-only; the synthetic CbzP comparator is added
  downstream at the analysis layer, so it is out of scope for an independent
  derivation by construction (consistent with `results_reconcile.R`).

## Finding — where admiral meets a study-specific rule (PFS)

admiral's `derive_param_tte()` models **event precedence** (earliest qualifying event
wins; censoring applies only if no event) and, given multiple `censor_source`s,
selects the **latest** censoring date. TROPIC's PFS SAP instead **censors at a new
anti-cancer therapy (NACT) *before* progression** — i.e. a censoring reason that must
*outrank* both a later progression and the last-evaluable date.

Modelling this directly with two competing censor sources produced **39 subjects**
where admiral censored at last-evaluable while the SAP requires NACT (event-vs-censor
classification, `CNSR`, was already identical — only the censor *date* differed). The
faithful fix pre-derives the single PFS censor date per the SAP hierarchy (NACT day
−1 outranks last-evaluable) and feeds admiral one `censor_source`. With that, PFS
reconciles exactly.

**Takeaway:** admiral cleanly covers OS and the PFS event model, but the study's
NACT-priority censoring is a genuine extension point — a useful, concrete example of
where a standard toolkit needs a study-specific pre-step rather than a config flag.

## Not wired into the gated CI build

This is a runnable, self-checking demonstration track (it writes its own status
JSON). It is intentionally *not* added to `cibuild.py`'s gated stages yet: that would
require `admiral` in the CI renv lockfile. Left as a deliberate follow-up.
