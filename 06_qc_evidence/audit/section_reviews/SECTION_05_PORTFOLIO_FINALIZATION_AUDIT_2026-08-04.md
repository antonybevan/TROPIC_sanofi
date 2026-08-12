# Section 5 — Portfolio finalization and connected-evidence audit

**Review date:** 2026-08-04  
**Product claim:** Path A controlled non-submission demonstration  
**Accountable author:** Antony Bevan  
**Review mode:** AI-assisted independent-style technical challenge under a
single-author portfolio model  
**Regulated-use decision:** **NO-GO**

> **External-validation addendum — 2026-08-12.** A later definitive Pinnacle 21
> Community 4.1.0 / FDA 2508.1 run processed seven ADaM datasets and 121,320 records
> with zero rejects. It retained 30 open issue groups / 2,373 occurrences and an
> incompatible-CLI caveat. Licensed Enterprise and independent disposition approval
> remain absent, so the regulated-use decision is unchanged.

## Decision

**CONDITIONAL GO for portfolio release, effective only when the current commit
passes the full real-SAS DAG, committed release reseal, offline verification,
and GitHub CI.**

This audit is a technical quality review, not a sponsor approval, qualified
human independent review, medical opinion, professional credential, Part 11
signature, or authorization for regulated or patient-care use.

## Audit scope and result

| Section | Objects challenged | Result |
|---|---|---|
| Governance | Product claim, SAP lock, findings, statistical decisions | PASS within Path A |
| Source/SDTM | Source precision, CRF grounding, CORE residual controls | PASS with disclosed external residuals |
| Populations/endpoints | ITT/safety/measurable sets, T-11 mapping, F-042 | PASS; regulated external review still required |
| ADaM | Seven datasets, SAS/R parity, admiral core, endpoint semantics | PASS on current controlled evidence |
| Metadata/ARM | ADaM spec, Define-XML, VLM/where clauses, ARM results | PASS after remediation |
| TFL/QC | 21 controlled outputs, four table bundles, seven primary figures, reconciliations | PASS after remediation |
| Reviewer/package | ADRG/SDRG/BDRG, traceability, Module 5-style package | PASS within non-submission claim |
| Release | DAG, manifest, RC checklist, offline verification, CI | Machine-controlled; GO is effective only when the promotion rule below passes |

## Findings opened and remediated

### PF-01 — ADaM specification presentation

The governing workbook was structurally valid but visually unfit for efficient
review: important headers and values were clipped across multiple sheets.

**Resolution:** all ten sheets now use consistent professional typography,
header styling, widths, wrapping, freeze panes, borders, and review-friendly
row heights. The workbook was re-imported, formula-error scanned, and rendered
sheet by sheet. Governed content remains 7 datasets and 159 variables.

### PF-02 — Define-XML/ARM endpoint truth

The prior ARM carried stale SAP v3.0 wording, described TTUMOR as a
measurable-disease analysis rather than ITT-primary, omitted TTPAIN and
promoted response/Optimus results, and did not fully declare survival
covariates or controlled TFL bindings.

**Resolution:** Define-XML now contains 10 ResultDisplays and 18
AnalysisResults, covering every controlled analysis output except F-01-1.
TTUMOR is ITT-primary; TTPAIN, response, safety, and Optimus result metadata
are present; OS/PFS declare ADSL covariates; display names bind to TFL IDs; and
each display carries the reconstructed/synthetic comparator limitation.
`platform/define_arm_contract.py`, G02, XSD/ARM validation, spec-to-Define, and
four negative-control tests enforce the corrected state. F-014 is resolved.

### PF-03 — TFL reviewer presentation

The PFS figure title extended beyond the rendered canvas, the swimmer figure
cut off its mandatory synthetic-data disclosure, and secondary TTE tables
printed non-estimable values as `NA`/`NA-NA` and very small p-values as
`0.0000`.

**Resolution:** title and caption layouts were corrected without weakening the
detached-artifact disclosure. Tables now use `NE` and `<0.0001`. The population
contract, statistical snapshots, results reconciliation, forest
reconciliation, figure-data reconciliation, and figure-canvas checks pass.

### PF-04 — Active-record drift

Several active governance records retained the earlier 18-in-scope /
21-deferred catalog counts and the former 8-display/10-result ARM disposition.

**Resolution:** the findings board, residual-risk memo, workstream boards,
population control, script map, TFL index, and traceability matrix now agree on
21 controlled outputs, 18 deferred SAP outputs, and 10 displays / 18 results.
Historical tagged records remain unchanged as historical evidence.

## Evidence connection

```text
SAP v4.0 + endpoint decisions
  -> ADaM specification and separate SAS/R derivations
  -> dataset/results/endpoint reconciliation
  -> Define-XML/ARM + executable contract
  -> controlled TFL catalog + physical output index
  -> ADRG/SDRG/BDRG + traceability
  -> Module 5-style package
  -> release manifest, checklist, offline verification, CI
```

Each arrow is represented by an executable gate or a controlled review record.
Green evidence proves coherence only within the declared Path A scope.

## Residual risks that remain accepted

1. CbzP is reconstructed/synthetic and TFL-only; comparative conclusions are
   non-confirmatory.
2. N=749 is not protocol ITT N=755.
3. The public source has precision and domain-breadth limitations.
4. Licensed, qualified P21 Enterprise validation is absent; Community and broader conformance findings remain open.
5. ARS, Dataset-JSON, and USDM are partial/exploratory layers.
6. EXAMPLE eCTD identifiers, incomplete aCRF depth, and non-Part-11 controls
   preclude a filing claim.
7. The single-author model provides implementation challenge, not
   organizational independence. Qualified statistical and medical review is
   still required before any regulated reuse.

## Promotion rule

The conditional portfolio GO becomes effective only when all of these are true
for the same committed source state:

- 34/34 real-SAS DAG stages PASS with no `NOT_RUN`;
- exact subject-level `F042_PAIN_RESPONSE` SAS/R parity PASS;
- all conformance, TFL, package, log, and reviewer gates PASS;
- release-run manifest has `release_candidate` evidence grade;
- `scripts/verify_release.py` passes;
- GitHub CI passes on the release commit.

Until then, this record remains a conditional technical disposition.
