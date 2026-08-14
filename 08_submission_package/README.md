# TROPIC Module 5 Review Package

This directory is the reviewer-facing surface of the TROPIC controlled clinical-submission simulation. The numbered folders elsewhere in the repository are the production and evidence factory; they are not presented as an eCTD submission.

**Current controlled release:** [`docs/RELEASE_NOTE_v0.3.0-clinical-simulation.md`](../docs/RELEASE_NOTE_v0.3.0-clinical-simulation.md) · tag `v0.3.0-clinical-simulation`

## Fitness statement

The package is fit for technical review of a submission-style clinical programming workflow. It is not a regulatory submission, FDA acceptance evidence, a Part 11 validated execution, licensed Pinnacle 21 Enterprise clearance, or independently approved QC.

## Open in this order

| Step | Artifact | Review purpose |
|---:|---|---|
| 1 | `m5/datasets/tropic/analysis/adam/adrg.pdf` | ADaM scope, derivations, traceability, validator findings, and known differences |
| 2 | `m5/datasets/tropic/tabulations/sdtm/csdrg.pdf` | Source SDTM boundary and data-standard decisions |
| 3 | `m5/datasets/tropic/analysis/adam/datasets/define.xml` | ADaM metadata and ARM with local stylesheet |
| 4 | `m5/datasets/tropic/tabulations/sdtm/datasets/define.xml` | SDTM metadata with separate local stylesheet |
| 5 | `m5/53-clin-stud-rep/.../tropic/csr.pdf` | Controlled narrative and output appendices |
| 6 | `m5/datasets/tropic/bimo/datasets/bdrg.pdf` | BIMO/clinsite explanation |
| 7 | `m5/53-clin-stud-rep/.../tropic/simulation-model-analysis-plan.pdf` | Informative, prospectively governed simulation protocol and acceptance criteria |
| 8 | `m5/53-clin-stud-rep/.../tropic/simulation-report.pdf` | Generated simulation operating characteristics, precision accounting, and limitations |
| 9 | `ectd/0000/` | Example eCTD v3.2.2 sequence and STF backbone |

## Package contract

```text
m5/
  datasets/tropic/
    tabulations/sdtm/
      datasets/define.xml + define2-1.xsl + SDTM XPTs
      csdrg.pdf
      blankcrf.pdf                  source blank CRF; not annotated
    analysis/adam/
      datasets/define.xml + define2-1.xsl + ADaM XPTs
      programs/                     SAS/R programs plus plain-text Python/YAML simulation sources
      adrg.pdf
    bimo/datasets/
      clinsite.xpt
      bdrg.pdf
  53-clin-stud-rep/.../tropic/
    csr.pdf + controlled tables and figures
    simulation-model-analysis-plan.pdf + simulation-report.pdf
```

The package generator enforces the FDA June 2026 cSDRG filename `csdrg.pdf`. The legacy `sdrg.pdf` path fails the regulatory-baseline gate. `blankcrf.pdf` is classified as a source study-report document; it is not renamed or tagged as an annotated CRF.

## Data boundary

The packaged analysis datasets contain the real de-identified MP arm only. The reconstructed/synthetic CbzP comparator is used only for descriptive TFL demonstrations and does not appear as reconciled ADaM. Patient-level source and derived XPTs are intentionally excluded from a clean public Git clone.

## Validation evidence

| Layer | Evidence | Interpretation |
|---|---|---|
| Programming | Real SAS ODA plus independent R derivation; selected admiral corroboration | Technical implementation evidence |
| Reconciliation | Key, value, population, and result-level gates | Controlled-scope agreement |
| Metadata | XSD, Define checks, ARM contract, spec-to-Define and spec-to-data | Local standards conformance |
| Pinnacle 21 | Community 4.1.0 / FDA 2508.1; 7 datasets, 121,320 records, 0 rejects, 30 open groups / 2,373 occurrences | Informative issue-discovery evidence only; compatibility caveat retained and Enterprise not executed |
| Package | PDF structure, fonts, bookmarks, links, STF classification, checksums, backbone validation | Structural simulation |
| Simulation methods | Governed protocol, deterministic scenario seeds, analytic null benchmark, complete replicate accounting, MCSE and Wilson intervals | Informative methods-evaluation only; not MIDD, confirmatory efficacy, a sponsor-approved design, or a clinical decision |
| Release | SHA-256 manifests, CI, clean-checkout verifier | Integrity and reproducibility, not Part 11 |

See [`docs/QUALITY_SYSTEM_BOUNDARY.md`](../docs/QUALITY_SYSTEM_BOUNDARY.md) for the exact work required before regulated reuse.

## Rebuild

After a successful data-bearing pipeline run:

```bash
python3 platform/package_ectd.py
python3 platform/build_ectd_backbone.py
python3 platform/materialize_ectd.py
python3 platform/check_regulatory_baseline.py --check-only
python3 platform/check_gate_g07_reviewer_package.py --check-only
```

The canonical build commands fail on missing source artifacts, stale metadata, invalid reviewer PDFs, unclassified required leaves, legacy cSDRG naming, or a false aCRF alias.
