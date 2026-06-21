# Upstream contribution: cdisc-org/cdisc-rules-engine

**Status: SUBMITTED — [PR #1770](https://github.com/cdisc-org/cdisc-rules-engine/pull/1770)**
(branch `fix/standardtypes-adam-products`, base `main`, author antonybevan, DCO signed).

## What it fixes

`StandardTypes` is the allow-list the CLI uses to validate `-s/--standard`; `core.py`
rejects any value not in `StandardTypes.values()`. On `main` it lists `adamig` but not
the other six ADaM products in `ADAM_PRODUCTS` (`adam-adae`, `adam-md`, `adam-nca`,
`adam-occds`, `adam-tte`, `adam-poppk`), which `normalize_standard_input()` already
handles. So `-s adam-tte` is rejected before the engine runs. The PR adds the six
products to the enum and a test that keeps the gate in sync with `ADAM_PRODUCTS`,
completing the normalization begun in PR #1733.

## Verification (against `main`, 2026-06-21)

- The original `-s adamig` gate fix is already upstream (PR #1733, merged 2026-06-05),
  so it was not resubmitted.
- `StandardTypes` lists `adamig` only; `ADAM_PRODUCTS` lists all 7;
  `normalize_standard_input()` maps all 7; `core.py` hard-exits on unlisted values.
  The six-product gap is therefore real and the fix is additive.
- No open PR duplicated it.
- `black` and `flake8` pass on both changed files; the new test passes.

## Files (local record)

| File | Purpose |
|---|---|
| `0001-sync-adam-products-into-standardtypes.patch` | The fix as a standalone patch (as submitted). |
| `PR_sync-adam-products.md` | Draft PR body (the live PR body is equivalent). |
| `ISSUE_same-operator-same-dataset-collision.md` | A separate engine bug (same-operator/same-dataset operation-result cache collision), prepared but **not yet filed**. Reproduction and diagnosis only. |

## Not contributed: the `TROPIC-ADAM-###` rules

The seven local rules in `../conformance_rules/adam/` are a seed pack (key-variable
population) with placeholder IDs. They are not upstream-contributable: CDISC authors
its rule pack from the official ADaM Conformance Rules spreadsheet under governed
`AD####` IDs. The engine fix in PR #1770 is the contribution.
