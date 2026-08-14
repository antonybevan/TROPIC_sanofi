# Contributing

This repository contains a controlled clinical-submission simulation and its reproducible factory.
Contributions should keep the review surface, evidence boundary, and release controls explicit.

## Before opening a pull request

- Keep patient-level data, licensed source material, credentials, and generated runtime output out
  of Git. Use synthetic or data-free fixtures for tests.
- Read [`docs/PRODUCT_CLAIM.md`](docs/PRODUCT_CLAIM.md) and
  [`docs/REPO_SURFACE_POLICY.md`](docs/REPO_SURFACE_POLICY.md) before changing a controlled
  surface.
- Run `python3 scripts/verify_release.py` and `python3 -m pytest -q` when the local prerequisites
  are available. For R-facing changes, run the affected `Rscript` test files as well.
- Run `git diff --check`. Run the repository pre-commit hooks and the pinned gitleaks check when
  those tools are installed.
- Explain any unavailable dependency, licensed input, SAS/ODA execution, or stale seal in the PR
  description. Do not weaken a gate to make a check green.

## Change and review expectations

Use a focused branch and a focused commit/PR. Changes to `config/`, `00_governance/`, release
seals, submission material, or validation controls require review by the repository owner before
they are presented as a release. Keep generated reports reproducible from their source data and
configuration; do not hand-edit a machine status file to change its result.

Pull requests should state:

1. the user-visible or control-plane outcome;
2. the files and evidence affected;
3. the commands and environments used for validation; and
4. remaining limitations, including whether real SAS/ODA and licensed data were unavailable.

## Branches and releases

Use a descriptive `codex/` or feature branch, rebase or merge the current target branch before
handoff, and open a draft PR when a required external run or owner decision is still outstanding.
Release promotion is allowed only after `scripts/verify_release.py`, the applicable data/QC gates,
and the source/artifact hash seal agree. A demo, cached run, or data-free simulation is informative
and must retain its explicit provenance label.
