# TROPIC — Pipeline Orchestrator Assurance Rationale

**Study EFC6193 / XRP6258 (TROPIC, NCT00417079)** · Companion to
[RISK_BASED_VALIDATION.md](RISK_BASED_VALIDATION.md) and ADRG §6.

> **Purpose.** `RISK_BASED_VALIDATION.md` states how much *statistical* validation each
> clinical output receives and why. This document is its engineering counterpart: it
> states why each control built into the pipeline **orchestrator**
> (`06_telemetry/cibuild.py`, `oda_broker.py`) exists, which failure mode it closes, and
> why the chosen assurance activity is proportionate to that failure's consequence —
> rather than reading as an unexplained pile of defensive code.

## 1. Scope and regulatory grounding

The orchestrator is a bespoke, single-purpose build/QC tool (GAMP 5 Category 5:
custom software) that sequences the R/SAS validation tracks, gates promotion of
`04_adam/*.xpt`, and writes the run record a reviewer inspects. It is not itself a
statistical method — ICH E9 and the tiering in `RISK_BASED_VALIDATION.md` govern that —
so its assurance question is the GAMP 5 one: **is the *effort* spent on each control
proportionate to what goes wrong if that control is absent or defeated?**

**A scope note, stated explicitly to avoid a common miscitation:** FDA's Computer
Software Assurance (CSA) final guidance (September 2025) is scoped to computerized
systems used in **production and quality-system processes** under 21 CFR Part 820 and
explicitly excludes SaMD/SiMD; it does not govern a GCP clinical-data reduction
pipeline. The risk-based reasoning below is grounded instead in **GAMP 5 (2nd edition,
2022)**, whose risk-based, GxP-wide approach to computerized system validation does
apply here, and in the general industry move away from documentation-volume-as-proof
toward proportionate, risk-targeted assurance activities.

## 2. Control → failure mode → assurance rationale

| Control | Failure mode it closes | Consequence if absent | Assurance activity (proportionate to consequence) |
|---|---|---|---|
| Honest `sas_execution_mode` labeling (`oda`/`local`/`cached`/`sim`) | A no-engine (`sim`) run being read as genuine double-programming | Highest — the pipeline's central evidentiary claim becomes false | Every mode is recorded and printed explicitly (`_resolve_sas_mode`); `sim` is labeled tautological in the same run, not after the fact |
| Byte-distinctness provenance guard + SDTM-manifest-SHA binding (`write_telemetry`) | A stale or restamped GREEN snapshot being presented as a fresh independent SAS run | High — an unearned reliability claim, uncheatable only if the check is real | Deterministic, no-exception check on every `oda`/`local` run; failure forces `pipeline_health_status = RED`, not a warning |
| Live ODA nonce probe (`oda_broker._default_prober`) | A dead/cached session being mislabeled `oda` | High (feeds directly into the guard above) | A fresh runtime nonce must round-trip through the live workspace before `oda` mode is ever recorded |
| Name-keyed post-execution QC gates + F-6 startup assert + `gated ∧ parallel` assert | A stage rename/renumber (or a gated stage becoming parallel) silently detaching its QC gate | High — a corrupted/incorrect deliverable proceeds ungated (the C-3 regression class, observed in practice) | Static assertion at pipeline start, before any stage executes — a wiring error is a hard fail, not a runtime surprise |
| Unconditional pre-run backup (`create_backup()`, hoisted out of the stage loop) | `--from-stage N>1` skipping the backup, so a later failure's rollback finds nothing to restore and silently no-ops while reporting success | High — "reports success while doing nothing" is a worse failure mode than no control at all | Backup is now taken once, unconditionally, regardless of which stage the run starts from; `rollback()` also reports honestly when there is nothing to restore |
| Per-stage execution timeout (`STAGE_TIMEOUT_S`) | A wedged `Rscript`/`logrx::axecute` blocking the pipeline (or one parallel worker) indefinitely | Medium — availability/operability, not data integrity | A bounded wall-clock cap turns an indefinite hang into an ordinary, rollback-triggering FAIL |
| `renv.lock` version-drift gate (`check_renv_lock.py`) | A local run's installed R packages silently drifting from the CI-restored, locked environment | Medium-High — undermines the pipeline's own reproducibility claim | Blocking pre-flight check against the packages the validation track actually requires, not the full transitive closure (avoids noisy, irrelevant failures) |
| Environment capture in telemetry (R version, `renv.lock` SHA256, SAS version) | "Reproducible on what?" being unanswerable from a given run's own record | Medium — a documentation/traceability gap, not a live defect | Captured every run, best-effort, never fails the build (an environment probe must not itself become a new failure mode) |
| Hash-chained append-only run log (`pipeline_health_log.jsonl`) | `pipeline_health.json` being silently overwritten every run, leaving no tamper-evident history beyond git log (which a rebase/force-push can rewrite) | Medium — an audit-trail gap under 21 CFR Part 11 §11.10(e) | Each entry embeds the SHA256 of the previous entry; editing or deleting any prior line breaks every downstream hash |
| Static evidence re-verifier (`verify_evidence.py`, its own CI step) | A committed "GREEN" evidence snapshot silently rotting or becoming internally inconsistent with no one re-checking it | Medium — a documented-but-unverified claim ages into an unverified one | Re-parses the committed snapshot for internal contradiction and cross-file consistency on every CI run; a stronger, diagnostic-only hot re-hash runs when real XPTs happen to be present locally, never gating on an expected, dated-snapshot mismatch |
| Guarded env-var integer parsing (`_env_int`) | A malformed override (e.g. `TROPIC_ODA_MAX_WAIT=foo`) crashing the run with a raw stack trace before anything executes | Low — operability, not data integrity | Falls back to the documented default with a printed warning |
| Content-hash stage-cache dry run (`_cache_dry_run_check`) | *(not yet a risk control)* — logged only, never skips a stage | None today by design | Deliberately advisory-only until its accuracy is proven across real runs; promotion to an authoritative skip is a separate, later decision |

## 3. Why this is proportionate, not exhaustive

The table above is ordered roughly by consequence, and the assurance activity scales
with it: controls guarding the pipeline's central evidentiary claim (execution-mode
honesty, the provenance guard, gate wiring) are hard, unconditional, build-blocking
checks; controls guarding operability (timeouts, malformed env vars) degrade gracefully
with a clear message; and a control with no proven failure mode yet (the stage cache)
is deliberately kept advisory rather than given authority it hasn't earned. This mirrors
GAMP 5's core instruction to concentrate assurance effort where the cost of failure is
highest, and to avoid spending equivalent effort on a low-consequence corner as on a
high-consequence one.

## 4. What this document is not

It is not a claim that the orchestrator is formally validated under a sponsor's
computerized-system-validation SOP, and it does not substitute for
`RISK_BASED_VALIDATION.md`'s statistical-output tiering. It is a concise, reviewable
rationale for why each existing engineering control exists — the GAMP 5 answer to "if
this control fails, what actually goes wrong, and does the effort spent match that" —
rather than a test-script binder asserting volume of activity as proof of assurance.

## References

- GAMP 5 (2nd edition, 2022) — risk-based approach to GxP computerized system validation.
- 21 CFR Part 11 §11.10(e) — audit trails must be tamper-evident.
- FDA Computer Software Assurance final guidance (September 2025) — scoped to 21 CFR
  Part 820 production/QMS software; noted here only to state why it is **not** cited as
  governing this pipeline.
- `RISK_BASED_VALIDATION.md` — the companion statistical-output risk tiering.
- ADRG §6 — validation mechanics and the single-programmer disclosure.
