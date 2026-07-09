# TROPIC Product Claim Decision

**Decision ID:** G00-PC-2026-07-09  
**Status:** Active  
**Decision owner:** Governance and scope control (WS-0)  
**Applies to:** current `main` operating model and the sealed demo release `v0.1.0-demo-rc.1`  
**Related board:** `docs/WORKSTREAM_EXECUTION_BOARD.md`

---

## 1. Product Claim In Force

TROPIC is a **controlled non-submission demonstration package**.

It demonstrates that a clinical programming repository can operate with:

- a full governed DAG;
- real independent SAS execution through ODA;
- SAS/R dataset and result reconciliation;
- a scoped third-engine admiral validation track;
- risk-based validation controls;
- metadata, traceability, TFL catalog, log-cleanliness, and release-evidence gates;
- a clean release-candidate seal for the controlled demo scope.

The current claim is **not** that this repository is an FDA filing package.

---

## 2. What The PASS Seal Means

For `v0.1.0-demo-rc.1`, `release_candidate=PASS` means:

- `pipeline_health` is `GREEN`, `oda`, `full_dag`, with 30/30 stages passing;
- `release_run_manifest` is `PASS` with `evidence_grade=release_candidate`;
- validation strategy, log cleanliness, metadata controls, TFL controlled catalog, and release checklist pass;
- active Critical/Major findings are either `RESOLVED` or formally `ACCEPTED` for the controlled demo claim;
- accepted residuals remain visible in `audit/FINDINGS_DISPOSITION_BOARD.md` and do not silently become filing-ready evidence.

This is a **release-candidate seal for the demo product claim**, not a regulatory submission attestation.

---

## 3. Claims Allowed In Public Or Interview Language

The following statements are permitted:

- "This is a controlled, non-submission clinical programming demo package."
- "The pipeline completed a full ODA-backed DAG with SAS/R reconciliation and a scoped admiral third-engine validation track."
- "The release manifest and release-candidate checklist passed for the controlled demo scope."
- "Residual submission-grade gaps are formally dispositioned rather than hidden."
- "The architecture models department-style handoffs across governance, source intake, specification, standards, programming, QC, writing, and release engineering."

---

## 4. Claims Not Allowed

The following statements are not permitted unless G00 is revised:

- "This is FDA submission-ready."
- "This is a validated Part 11 system."
- "The eCTD sequence is ready for agency filing."
- "The comparator-arm analyses are confirmatory trial evidence."
- "All CDISC/Pinnacle 21 findings are closed."
- "The SAP is sponsor-approved for filing."
- "The annotated CRF and application metadata are final."

These are outside the current product claim.

---

## 5. Accepted Residuals Under The Demo Claim

The current demo release accepts residuals only because they are controlled, disclosed, and not represented as filing-ready:

| Finding Area | Demo Decision |
| --- | --- |
| Synthetic/Guyot CbzP comparator content | Non-submission demo limit; comparative outputs are illustrative/non-confirmatory. |
| EXAMPLE eCTD metadata and placeholder CRF | External dependency and demo limit; true sponsor identifiers and aCRF are required for filing. |
| PSA population shell residual | Scoped out with disclosure; current controlled output uses documented ADRS PSARESP logic. |
| Protocol ITT N=755 vs package N=749 | Non-submission demo limit; full two-arm IPD required for original-trial ITT claims. |
| ARM, Dataset-JSON, USDM, ARS breadth | Controlled core or exploratory layers only; not full submission coverage. |
| Full P21/commercial validator evidence | External dependency; local spec/conformance controls are substitutes for the demo claim only. |
| SDTM CORE/date residuals | Source-data/conformance residuals disclosed; not silently closed. |
| Part 11 controls | Not claimed; organizational CSV, access, audit trail, and e-signature controls required. |

The authoritative residual record is `audit/FINDINGS_DISPOSITION_BOARD.md`.

---

## 6. Workstream Consequence

This decision means workstreams are judged against the **controlled demo claim** unless G00 changes.

| Workstream | Consequence |
| --- | --- |
| WS-0 Governance | Owns claim language and prevents drift into filing-ready wording. |
| WS-1 Source/CDM | Must disclose source precision and CORE residuals; no silent source-lock overclaim. |
| WS-2 Specification | Must separate SAP-controlled demo scope from deferred shells. |
| WS-3 Standards | Must label exploratory standards layers and external validator gaps. |
| WS-4 Programming | May stay GREEN only for the controlled catalog scope. |
| WS-5 QC/Validation | Must turn accepted findings into reviewer-readable known differences. |
| WS-6 Writing | Must make ADRG/SDRG/BDRG match this claim. |
| WS-7 Release Engineering | Maintains the seal; does not expand product meaning by itself. |

---

## 7. Change Control

Changing the product claim from **controlled non-submission demo** to **submission simulation** requires a new G00 decision and, at minimum:

- a real application/submission metadata path;
- true annotated CRF evidence;
- full sponsor-data boundary resolution for comparator claims;
- external validator/P21 evidence or documented unavailable status with residual disposition;
- hardened ADRG/SDRG/BDRG signoff;
- a known-differences memo accepted by WS-5 and WS-6;
- a fresh release-candidate seal after the changed evidence scope.

Until then, `v0.1.0-demo-rc.1` remains a controlled demo release, not a filing package.
