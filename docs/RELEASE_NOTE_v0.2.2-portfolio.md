# TROPIC Release Note — `v0.2.2-portfolio`

**Product:** Controlled clinical-biometrics programming portfolio  
**Study:** EFC6193 / XRP6258 (TROPIC, NCT00417079)  
**Release class:** Path A controlled non-submission demonstration  
**Release date:** 2026-08-05  
**Predecessor:** `v0.2.1-portfolio` (immutable)  
**Regulated-use status:** **NO-GO**

## Verdict

`v0.2.2-portfolio` closes the repository pipeline-integrity and release-governance
audit findings. It preserves the existing 34-stage real-SAS evidence snapshot and
adds stronger controls around the code that verifies and promotes that snapshot.

The clinical stages were not re-executed during this governance closure: the local
ODA attempt was stopped after repeated authentication/spawn failures. That boundary
is recorded in `platform/pipeline_health.json` as a governance-only seal rebind; no
clinical dataset, QC result, or package output was changed by the closure.

## Closure changes

- `scripts/verify_release.py` now rehashes present sealed QC, TFL, package, additive,
  input, log, and dataset artifacts; present ignored artifacts cannot silently drift.
- The release seal binds the exact 34-stage set and pipeline-control files, including
  CI, dependency locks, CODEOWNERS, and verifier code.
- `platform/cibuild.py --validate-dag` and the CI regression test validate stage order,
  script presence, gate wiring, and parallel boundaries before smoke tests.
- GitHub Actions, Gitleaks, Python dependencies, and R bootstrap versions are pinned;
  live CDISC CT credentials are isolated to a trusted/manual job.
- The existing `v0.2.1-portfolio` tag remains untouched; this successor tag is the
  current release identity.

## Reviewer re-check

```bash
python3 scripts/verify_release.py
python3 platform/cibuild.py --validate-dag
python3 -m pytest -q tests/test_verify_release.py tests/test_pipeline_dag.py
```

This remains a Path A portfolio demonstration, not an FDA submission, sponsor-approved
analysis, independent clinical confirmation, validated Part 11 system, or source of
patient-care evidence.
