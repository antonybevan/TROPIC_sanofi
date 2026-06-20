# Upstream contributions → `cdisc-org/cdisc-rules-engine`

Prepared while authoring executable ADaM conformance rules for TROPIC. **Verified
against current upstream `main` (2026-06-20)** — not against a stale tag.

## Contents

| File | Kind | What |
|---|---|---|
| `0001-sync-adam-products-into-standardtypes.patch` | **PR (fix in hand)** | Adds the 6 ADaM products still missing from the CLI `StandardTypes` gate (`adam-adae`, `adam-md`, `adam-nca`, `adam-occds`, `adam-tte`, `adam-poppk`) so they match `ADAM_PRODUCTS` / `normalize_standard_input()`. |
| `PR_sync-adam-products.md` | PR body | Summary, reproduction, root cause (incomplete #1733 sync), test plan, DCO note. |
| `ISSUE_same-operator-same-dataset-collision.md` | **Issue (no fix)** | Two same-operator rules on the same dataset collide in the per-run operation-result cache. Reproduction + diagnosis only. |

## Verification (why this is real, not a waste)

Checked against `cdisc-org/cdisc-rules-engine@main`, not the local `v0.16.0` clone:

- **The original `-s adamig` gate bug is already fixed upstream** (PR #1733, merged
  2026-06-05). That headline fix is *gone* — do not resubmit it.
- **`StandardTypes` (main)** has `adamig` but still omits the other 6 ADaM products.
- **`ADAM_PRODUCTS` (main)** still lists all 7.
- **`normalize_standard_input()` (main)** still maps all 7 via `ADAM_PRODUCTS`.
- **`core.py`** hard-exits (`ctx.exit(2)`) on any `-s` value not in
  `StandardTypes.values()`.
- ⇒ `-s adam-tte` (and the 5 others) are rejected despite full engine support. The
  6-line additive fix completes #1733's normalization. **No open PR duplicates it.**
- Patch verified to `git apply` cleanly to current `main`; patched file parses.

This is a **minor, correct, mergeable** consistency fix — submitted for the durable
"contributor to `cdisc-org/cdisc-rules-engine`" credential, not for novelty (the
novel `adamig` window has closed).

## Why not the `TROPIC-ADAM-###` rules

The seven local rules in `../conformance_rules/adam/` are a seed pack (key-variable
population) with placeholder IDs — **not** upstream-contributable (CDISC's pack is
authored from the official ADaM Conformance Rules spreadsheet under governed `AD####`
IDs). The engine fix here is the real contribution.

## How to submit (manual — `gh` not available in this environment)

Submitting publishes under your GitHub identity with your DCO sign-off, so this is
left for you to drive:

```bash
# Fork cdisc-org/cdisc-rules-engine on GitHub, then:
git clone https://github.com/<you>/cdisc-rules-engine && cd cdisc-rules-engine
git checkout -b fix/sync-adam-products-into-standardtypes
git apply /path/to/0001-sync-adam-products-into-standardtypes.patch
git commit -s -am "fix(cli): sync remaining ADaM products into StandardTypes (follow-up #1733)"
git push -u origin fix/sync-adam-products-into-standardtypes
# Open the PR using PR_sync-adam-products.md as the body.

# Separately, open the cache-collision issue using
# ISSUE_same-operator-same-dataset-collision.md as the body.
```
