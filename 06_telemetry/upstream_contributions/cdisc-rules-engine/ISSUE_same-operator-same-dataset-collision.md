# Issue: two same-operator rules on the same dataset collide in the operation-result cache

**Target repo:** `cdisc-org/cdisc-rules-engine`
**Observed on:** CORE 0.16.0
**Type:** Bug report (no fix proposed — reproduction + diagnosis only)

## Description

When two rules use the **same operator** against the **same dataset** in a single
`validate` invocation, the second rule reports an execution error instead of its
result. Each rule validates correctly **in isolation**; the failure only appears
when both run together. The symptom is consistent with the per-run
operation-result cache keying on (dataset, operator) without disambiguating by
rule/variable, so the second rule reads the first rule's cached operation result.

## Reproduction

1. Author two local rules targeting the same ADaM dataset (e.g. `ADSL`), both
   using `operator: empty` on different variables.
2. Run them together via `core validate ... -lr <dir-with-both-rules>`.
3. The first rule reports normally; the second reports an execution error.
4. Run each rule alone → both succeed.

## Workaround in use

We structure the local ADaM pack as **one rule per (dataset, operator)** per
invocation, which sidesteps the collision. This is a workaround, not a fix —
real rule packs legitimately apply the same operator to several variables of one
dataset.

## Suggested investigation

Check the operation-result cache key construction for the operator-execution path:
it likely needs to include the operation's target variable(s) / rule identity, not
just (dataset, operator), so distinct operations on the same dataset don't alias.

## Notes

Reported as part of authoring executable ADaM conformance rules against CORE while
the official `adamig` rule pack is empty (CORE v1.0, ADaM listed under "What
Follows v1.0"). Happy to provide the two minimal colliding rule YAMLs on request.
