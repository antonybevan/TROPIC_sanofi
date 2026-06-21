# PR: sync remaining ADaM product standards into `StandardTypes` (follow-up to #1733)

**Target repo:** `cdisc-org/cdisc-rules-engine`
**Base:** `main`
**Patch:** [`0001-sync-adam-products-into-standardtypes.patch`](./0001-sync-adam-products-into-standardtypes.patch)

## Summary

`StandardTypes` (`cdisc_rules_engine/enums/standard_types.py`) is the CLI gate for
`-s/--standard`: `core.py` rejects (`ctx.exit(2)`) any standard not in
`StandardTypes.values()` when `--custom-standard` is not used. PR #1733
("normalize standards") synced this gate with the supported sub-products — it added
the `sendig-*` family and `adamig`. It did **not** add the other six ADaM products,
which are still listed in `ADAM_PRODUCTS` and still handled by
`normalize_standard_input()`:

```python
# cdisc_rules_engine/utilities/utils.py (current main)
if standard_lower in ADAM_PRODUCTS:
    return "adam", f"{standard_lower}-{version}"
```

```python
# cdisc_rules_engine/constants/adam_products.py (current main)
ADAM_PRODUCTS = ["adamig", "adam-adae", "adam-md", "adam-nca",
                 "adam-occds", "adam-tte", "adam-poppk"]
```

So `-s adam-adae`, `-s adam-md`, `-s adam-nca`, `-s adam-occds`, `-s adam-tte`,
`-s adam-poppk` are rejected by the gate even though the engine normalizes them
correctly (e.g. `adam-tte` → `("adam", "adam-tte-<version>")`). This PR adds those
six members to `StandardTypes`, completing #1733's normalization so the gate matches
`ADAM_PRODUCTS` and `normalize_standard_input()`.

## Reproduction (current `main`)

```bash
core validate -s adam-tte -v 1-0 -d <adam_xpt_dir> -ft xpt ...
# -> "Standard 'adam-tte' is not a supported standard." ; exit 2
#    despite normalize_standard_input() mapping it to ("adam","adam-tte-1-0")
```

## The change

```diff
     ADAMIG = "adamig"
+    ADAM_ADAE = "adam-adae"
+    ADAM_MD = "adam-md"
+    ADAM_NCA = "adam-nca"
+    ADAM_OCCDS = "adam-occds"
+    ADAM_TTE = "adam-tte"
+    ADAM_POPPK = "adam-poppk"
     TIG = "tig"
     USDM = "usdm"
```

Additive, one file, no behavioural change to existing standards. The six values are
copied verbatim from `ADAM_PRODUCTS`.

> **Optional follow-up (not in this PR):** `ADAM_PRODUCTS` and the ADaM members of
> `StandardTypes` must stay in sync by hand; they could be derived from a single
> source. Left out to keep this change minimal.

## Test plan

- `git apply` against a clean `main` checkout — applies cleanly; file parses.
- All seven ADaM products present in `StandardTypes` after patch.
- `core validate -s adam-tte -v 1-0 ...` proceeds past the gate (verified locally).
- Existing standards (`sdtmig`, `sendig*`, `adamig`, `tig`, `usdm`) unaffected.

## DCO

CDISC requires a Developer Certificate of Origin sign-off. Commit with `git commit -s`
so your own `Signed-off-by: Name <email>` is added — this file intentionally does not
fabricate one.
