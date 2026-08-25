# Release Promotion, No-Go, and Rollback Runbook

This is the single operator sequence for the conditional
`v0.3.0-clinical-simulation` candidate. It is a controlled simulation release,
not an FDA submission, electronic signature, Part 11 attestation, or sponsor
approval.

## 1. Entry criteria and preflight

1. Work on a reviewed branch with an empty material worktree:

   ```bash
   git status --porcelain=v1
   git rev-parse HEAD
   python3.12 --version
   Rscript --version
   ```

2. Confirm that local source data and ODA/SAS credentials are authorized,
   untracked, nonsymlinked where required, and mode 0600. Never print credential
   contents into a log or PR.
3. Restore the controlled environments using
   [`ENVIRONMENT_BOOTSTRAP.md`](ENVIRONMENT_BOOTSTRAP.md).
4. Review `docs/PRODUCT_CLAIM.md`, the findings register, the conditional release
   note, and the current `platform/pipeline_health.json` before execution.

Any failed prerequisite is a **NO-GO**. Record it; do not relabel cached or
simulated output as genuine evidence.

## 2. Execute and bind one genuine run

Use the ODA seed only when its manifest is absent or stale, then run the complete
DAG from stage 1:

```bash
python3.12 platform/seed_sdtm.py
python3.12 platform/cibuild.py --real-sas
```

The run must earn `sas_execution_mode=oda` or `local`, `run_scope=full_dag`, a
GREEN pipeline, genuine SAS-versus-R reconciliation, and all required stages.
`sim`, `cached`, `partial_dag`, or a failed external handshake is a **NO-GO**.

After the full run succeeds, rebuild the package and live control surfaces through
their generators; do not hand-edit status JSON:

```bash
python3.12 platform/package_ectd.py
python3.12 platform/build_delivery_controls.py
python3.12 platform/build_release_run_manifest.py
python3.12 platform/build_release_candidate_checklist.py
python3.12 scripts/verify_release.py
bash scripts/verify_release.sh
```

Inspect all changed figures and rendered PDFs, verify embedded fonts and checksums,
and reconcile the eCTD inventory. A PASS manifest produced from a dirty tree is not
acceptable; commit the controlled inputs, rerun from the clean commit, then bind
the final generated surfaces as designed.

## 3. Pull request and default-branch promotion

1. Push the candidate commit and open a **draft** PR while any external run,
   owner decision, or protected check is outstanding.
2. The PR description must state exact commands, run mode/scope, check results,
   external limitations, and current seals. It must not quote superseded GREEN
   evidence as the live state.
3. Require review of code, scientific changes, generated artifacts, findings
   disposition, and claim language. Do not approve your own controlled release.
4. Require all configured branch-protection contexts. Qualification, dependency,
   CodeQL, and functional checks must be independently visible; never combine a
   red qualification boundary into a misleading green aggregate.
5. Merge only when the PR is current with its base and every required context is
   green. Re-run the same protected checks on the default-branch commit.

## 4. Tag and verify

Create the annotated tag only from the verified default-branch commit:

```bash
git switch main
git pull --ff-only
python3.12 scripts/verify_release.py
git tag -s v0.3.0-clinical-simulation -m "TROPIC v0.3.0 controlled clinical simulation"
git show --show-signature --no-patch v0.3.0-clinical-simulation
git push origin v0.3.0-clinical-simulation
git ls-remote --tags origin v0.3.0-clinical-simulation
```

If signed tags are unavailable under the repository's documented identity policy,
stop for owner disposition; do not silently substitute an unsigned promotion tag.
The tag and a GitHub Release are separate records. If a GitHub Release is used,
its notes and attached checksums must be read back and compared with the tag.

## 5. No-go and rollback

- On any failed gate, leave the PR draft and the candidate untagged. Preserve the
  failed telemetry and logs as current evidence; preserve an earlier success only
  under the historical evidence namespace.
- Never copy an old PASS manifest over current RED telemetry, manually flip a
  status, suppress a qualification test, force-push a historical tag, or reseal a
  clinical/program change through a governance-only path.
- If a bad commit is merged but no tag was published, revert it with a reviewed
  PR and repeat the full sequence.
- If an incorrect tag was published, stop distribution, document the incident,
  publish a corrected successor tag after review, and mark the incorrect release
  as withdrawn. Do not move or overwrite the immutable tag silently.
- Restore artifacts only from a verified commit/tag whose hashes and provenance
  are intact. Then run the clean-checkout verifier again.

## 6. Promotion record

Record the commit SHA, tag object/signature, pipeline timestamp and mode, manifest
seal, release-candidate verdict, CI run URLs, reviewer approvals, known residuals,
and rollback disposition in the release notes. Organizational quality-unit,
medical/statistical, privacy, legal/data-rights, licensed-validator, and gateway
approvals remain external and cannot be manufactured by this repository.
