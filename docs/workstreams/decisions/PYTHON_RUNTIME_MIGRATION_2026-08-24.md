# Python runtime migration record — 2026-08-24

## Decision

The controlled Python runtime for local engineering and GitHub Actions is
**CPython 3.12.13**. The exact local selector is `.python-version`; every
`actions/setup-python` use in the primary CI workflow uses the same patch release.

This is an engineering lifecycle and reproducibility decision. It is not validation
of SAS, R, a sponsor computerized system, or a 21 CFR Part 11 environment.

## Rationale

- Python 3.10 reaches end of life in October 2026, leaving insufficient lifecycle
  margin for a production-grade portfolio maintained in August 2026.
- Python 3.12 is supported for security fixes through October 2028.
- SASPy 5.107.1 declares Python 3.x as a prerequisite, and the repository's genuine
  ODA preflight and broker have already executed from the local Python 3.12.13
  environment. The current ODA encryption-handshake outage reproduced independently
  and is not evidence of a Python compatibility failure.
- Moving from 3.10 to 3.12 is smaller and more conservative than adopting the newest
  language series while still removing the imminent end-of-life risk.

Official lifecycle sources:

- [Python supported versions](https://devguide.python.org/versions/)
- [Python 3.12 release schedule (PEP 693)](https://peps.python.org/pep-0693/)
- [SASPy official repository and prerequisites](https://github.com/sassoftware/saspy)

## Controlled dependency surface

`requirements-ci.lock` retains the reviewed package versions and changes only the
platform-specific hashes required by CPython 3.12 on Ubuntu x86_64. Each compiled
package is bound to the exact compatible wheel selected from the supported
`manylinux_2_17`, `manylinux_2_24`, `manylinux_2_27`, or `manylinux_2_28` tags.
Pure-Python wheels and the two explicitly allowed source archives retain their prior
hashes. `requirements-ci-build.lock` remains the separately hash-locked build backend;
build isolation remains disabled.

The engineering runtime migration is accepted only when all of the following are true:

1. every locked Python 3.12/Linux artifact downloads with `--require-hashes`;
2. the clean functional collection passes with the two external-run qualification
   assertions explicitly deselected;
3. regulatory-source, readiness, release-policy, and repository-hygiene tests pass;
4. GitHub's `Run Tests & Conformance Gates` and both CodeQL jobs pass on the migration
   commit.

Release adoption additionally requires the next genuine full SAS run to refresh the
regulatory baseline and release seal against the migrated source tree. Until that
succeeds, the release remains blocked. The runtime migration must not be
governance-resealed onto older genuine-SAS evidence.

## Rollback and future review

Rollback requires restoring the prior interpreter pin and its matching artifact
hashes together; mixing an interpreter with another runtime's hashes is prohibited.
Reassess the supported Python line at least annually and before October 2028, or
earlier if a critical dependency or SASPy drops compatibility.
