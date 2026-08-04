# Path A Statistical Governance Assessment

**Record ID:** `PATHA-STAT-GOV-2026-08-04`<br>
**Version:** `1.0.0`<br>
**Assessment date:** 2026-08-04<br>
**Accountable author / project owner:** Antony Bevan<br>
**Assessment mode:** AI-assisted internal governance-style review under the disclosed single-author model<br>
**Decision:** **CONDITIONAL GO — Path A controlled non-submission demonstration only**<br>
**Regulated-use decision:** **NO-GO**

## 1. Decision and authority boundary

The controlled Path A implementation may be promoted only when the current source
tree passes the conditions in §7. The decision does not authorize sponsor, clinical,
regulatory, filing, or patient-care use.

This review applies sponsor/statistical governance discipline to the available
evidence, but it does not create a sponsor organization or an independent reviewer.
An AI system cannot hold sponsor accountability, verify professional licensure,
provide a Part 11 signature, or replace qualified human statistical and medical
judgment. Antony Bevan remains the accountable author. The human approval block in
§10 is intentionally unsigned.

## 2. Materials reviewed

- `docs/PRODUCT_CLAIM.md` and the Path A claim boundary.
- SAP v4.0 controlled draft, including rendered pages 7, 8, 11, 14, and 16:
  multiplicity, secondary endpoints, T-11 mapping, endpoint algorithms, and
  published validation targets.
- `EDR-F042-T11-8-2026-08-03`, the endpoint approval specification, CM/PR source
  qualification audit, impact appendix, and delayed second-pass record.
- SAS and R F-042 programs, ADTTE derivations, TFL generator, output catalog,
  CTQ/ARS mappings, reviewer guides, and known-differences register.
- Current full-DAG health, SAS/R and admiral reconciliation, log-cleanliness,
  package, release-manifest, CI, and PR evidence.

## 3. Statistical decision matrix

| Decision | Governance assessment | Path A disposition |
|---|---|---|
| `ED-01` cancer-related support | The no-later-than-confirming-visit boundary, RECIST/clinical support, exclusion of PSA-only certification, and no later backdating are explicit and traceable. | Accept |
| `ED-02` CM+PR radiotherapy union | Full PR is staged; direct-intent treatment text, prior/history exclusion, radiopharmaceutical exclusion, exact-date control, and CM/PR provenance are implemented. | Accept |
| `ED-03` source sensitivities | Primary diary-or-RT, diary-only, RT-only, and missing/partial-date inventories are retained. Current aggregate evidence is 45 primary subjects, 45 diary-only, 1 RT-only, 15 complete-date RT inventory records, and 1 missing/partial-date record. | Accept for Path A; non-confirmatory |
| `ED-04` SAP output IDs | `T-11-3` PSA response, `T-11-4` ORR, `T-11-5` pain response, `T-11-6` TTUMOR, `T-11-7` TTPSA, and `T-11-8` TTPAIN agree across catalog, physical output, CTQ, and reviewer-facing traceability. `T-11-8b` is explicitly supportive. | Accept |
| `ED-05` TTUMOR population | SAP Table 22 specifies ITT for `T-11-6`; the primary implementation carries 371 real MP and 378 reconstructed CbzP ITT records. Measurable disease remains supportive; ORR remains measurable-disease restricted. | Accept with synthetic-comparator disclosure |
| `ED-06` time origins | Efficacy TTE parameters start at `RANDDT`; TTSAE starts at `TRTSDT`. Code and reviewer wording agree. | Accept |
| `ED-07` pain algorithm | Baseline median PPI and mean analgesic score use 5-of-7 evaluability; progression uses `PPI +1` or analgesic-score `+25%` with positive baseline; the same component must persist at the immediately next scheduled evaluation at least 21 days later; terminal and missing-visit bridges are rejected. | Accept subject to the endpoint-level SAS/R gate below |

## 4. Major finding `GOV-STAT-01`

**Classification:** Major for Path A validation; potentially Critical if used for a
regulated claim.<br>
**Object:** SAP `T-11-5` pain response.

The SAS implementation joined the immediately next scheduled visit and required an
interval of at least 21 days, but its response flags were calculated only from the
initial visit. It did not verify that the confirming visit also met the same response
component. A controlled replay of that exact defective logic on the current real MP
data evaluates to 65 responder subjects instead of the correct 43, creating 22 false
positives.

The physical Path A table reported the correct R-derived result, 43/153 (28.1%), so
the displayed count was not changed by this finding. The previous claim that T-11-5
had an independent SAS/R challenge was invalid, however, because the controlled
aggregate file was generated only from the R result and the SAS subject set was not
compared.

## 5. Corrective and preventive action

1. The SAS response branch now evaluates the initial and confirming visits
   independently for PPI and analgesic-score response and requires the same component
   at both visits.
2. SAS exports a transient subject-level response set containing subject, event date,
   confirming date, response component, and both date sources.
3. The cross-language reconciliation compares that extract exactly to the R event set.
4. A current real-SAS run fails if the extract is missing or any record differs.
5. The transient patient-level file is deleted after comparison; only aggregate
   PASS/FAIL evidence remains in Git.
6. Release-manifest construction, the release-candidate checklist, and
   `scripts/verify_release.py` now require
   `endpoint_controls.F042_PAIN_RESPONSE=PASS`.
7. A negative-control run with one R-equivalent record deliberately removed produced
   `SAS n=42, R n=43, R-only=1` and correctly failed the reconciliation stage.

## 6. Endpoint and result interpretation

- The real MP pain-response result is 43/153 (28.1%) under the implemented Path A
  algorithm. CbzP remains `N/A` because no PN source exists; no response count is
  imputed.
- TTPAIN and PFS pain-event derivations were already reconciled through the full ADTTE
  record comparison; the T-11-5 defect did not alter the sealed ADTTE event set.
- Comparative CbzP efficacy estimates remain reconstructed or PH-scaled
  demonstration results. P-values are descriptive and cannot support clinical,
  confirmatory, benefit-risk, or regulatory conclusions.
- The combined N=749 is not the protocol ITT N=755.

## 7. Conditions that make the conditional GO effective

The conditional GO becomes effective only when all of the following are true for the
same current source tree:

- [ ] Full 34-stage DAG completes under real SAS (`oda` or local), with no `NOT_RUN`.
- [ ] Dataset reconciliation is non-simulated PASS.
- [ ] `endpoint_controls.F042_PAIN_RESPONSE=PASS` with 43 exact SAS/R subject records.
- [ ] TFL, results, figure, admiral, metadata, log, package, and reviewer gates pass.
- [ ] Release manifest is `PASS` at `release_candidate` grade.
- [ ] `scripts/verify_release.py` passes all checks.
- [ ] GitHub CI passes on the PR head.

These checkboxes are operational conditions, not handwritten attestations. Their
authoritative state is the current machine evidence, so this record does not require
editing after every rerun.

## 8. Residual risks and regulated-use blockers

The following remain accepted only within Path A:

- reconstructed/digitized Guyot CbzP and PH-scaled secondary endpoints;
- N=749 rather than the protocol N=755;
- incomplete aCRF/application identifiers and example eCTD metadata;
- no commercial P21 ADaM validation and broader CORE residuals;
- partial-date/time-origin source limitations;
- partial ARM/ARS and exploratory Dataset-JSON/USDM scope;
- no independent organization, medical reviewer, sponsor document control, validated
  environment, or Part 11 signature.

No amount of additional self-review converts these into sponsor approval.

## 9. Governance conclusion

**Path A:** conditional GO after §7 passes. The project is technically coherent and
reviewable within its declared non-submission boundary.

**Path B/C or regulated reuse:** no-go until a qualified external statistician and
medical reviewer review the endpoint rules and outputs, sponsor authority accepts the
residuals, source-data rights are established, commercial validation is completed as
required, and controlled signatures are obtained.

## 10. Human approval block

| Role | Name | Decision / signature | Date |
|---|---|---|---|
| Accountable author / project owner | Antony Bevan | Pending human signature | — |
| Qualified statistical reviewer | — | Required before regulated reuse | — |
| Qualified medical reviewer | — | Required before regulated reuse | — |
| Sponsor governance authority | — | Required before regulated reuse | — |
