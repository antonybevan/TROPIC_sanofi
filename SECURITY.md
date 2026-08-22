# Security policy

## Scope

This policy covers the source code, configuration, scripts, documentation, and release tooling
in this repository. The repository is a public portfolio and controlled simulation project; it is
not a validated production or clinical system.

Do not put patient-level data, source clinical records, ODA credentials, API keys, authentication
files, or other confidential material in an issue, pull request, commit, or security report.

## Reporting a vulnerability

Please report suspected vulnerabilities privately through GitHub's private vulnerability reporting
or security-advisory channel for this repository. If that channel is not enabled, contact the
repository owner through GitHub before making any public disclosure. Include a short description,
affected path and revision, reproducible steps using synthetic or data-free inputs, and the impact.

Allow a reasonable coordination period before public disclosure. Do not probe live ODA/SAS
accounts or third-party services as part of a report.

## Supported surface and response

The maintained surface is the current default branch and active pull requests. Reproducible
security fixes should include a regression test and preserve the repository's fail-closed release
controls. A report may be closed as out of scope when it requires excluded patient data,
credentials, an unavailable external service, or a claim outside this repository's stated product
boundary.

## Data and release boundary

Patient-level source and derived datasets are intentionally excluded from Git. Local credentials
(`_authinfo`, `.authinfo`, `sascfg_personal.py`, and `.env` files) must remain untracked and mode
0600. The release seal and `docs/PRODUCT_CLAIM.md` define what can be presented as evidence; a
green demo or data-free run must not be represented as a genuine SAS/ODA clinical execution.
