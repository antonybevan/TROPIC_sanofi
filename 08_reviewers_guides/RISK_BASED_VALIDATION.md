# TROPIC — Risk-Based Validation Plan

**Study EFC6193 / XRP6258 (TROPIC, NCT00417079)** · Companion to ADRG §6 (validation
mechanics) and the reconciliation telemetry under `06_telemetry/`.

> **Purpose.** This document states *how much* validation each output receives and
> *why*. The ADRG describes the validation machinery; this plan makes the
> **risk-proportionate allocation** of that machinery explicit, so a reviewer can see
> that QC effort is concentrated where the consequence of error is greatest — and can
> read the single-programmer disclosure in that context rather than as a blanket gap.

## 1. Principle — validation proportionate to risk

Independent double programming of *every* output is neither universal practice nor a
regulatory mandate. **ICH E9** governs statistical principles but does not require
two-programmer re-derivation; the field consensus has moved to **risk-proportionate
QC**, in which full independent re-derivation is reserved for high-risk outputs
(primary efficacy, key safety) and lighter, automated controls suffice for
lower-risk and structural items (PHUSE / industry risk-based-validation literature;
PMC "risk-proportionate approach to validation of statistical programming").

TROPIC applies this deliberately: the number and independence of validation engines
**escalates with the risk tier of the output**.

## 2. Validation tiers

| Tier | What qualifies | Validation applied | Independent engines |
|---|---|---|---|
| **T1 — Critical** | Primary efficacy (**OS, PFS**); ADSL (drives every population & anchor date) | Dual-language dataset reconciliation **+** numeric results-level reconciliation **+** a third `admiral` re-derivation | **3** (SAS · R · admiral) |
| **T2 — Important** | Secondary efficacy (**TTPAIN, TTPSA, TTUMOR, TTSAE**); response (**ADRS**) | Dual-language dataset reconciliation + numeric results-level reconciliation (TTE params) | 2 (SAS · R) |
| **T3 — Supporting** | Derived analysis datasets (**ADAE, ADCM, ADEX, ADLB**) | Dual-language cell-level reconciliation + spec→data conformance | 2 (SAS · R) |
| **T4 — Structural / metadata** | define.xml, controlled terminology, dataset structure/labels/types | Automated conformance only (XSD, CDISC CORE, spec→data); no manual re-derivation | n/a (tooling) |

Rationale for the tiering: an error in **OS** changes the headline benefit claim, so it
gets the most scrutiny (now three independent derivations); an error in a **label or
codelist** is caught deterministically by a schema/conformance engine and needs no
human re-derivation.

## 3. Output → tier → evidence map

| Output | Tier | Validation evidence (artifact) |
|---|---|---|
| ADSL | T1 | `cross_lang_audit` (SAS↔R, 0-diff) · `admiral_reconcile` ADSL 0-diff (`06_telemetry/admiral_reconciliation_status.json`) |
| ADTTE · OS, PFS | T1 | `cross_lang_audit` · `results_reconcile` (KM median/events/N, `results_reconciliation_status.json`) · `admiral_reconcile` OS+PFS 0-diff |
| ADTTE · TTPAIN/TTPSA/TTUMOR/TTSAE | T2 | `cross_lang_audit` · `results_reconcile` (per-parameter) |
| ADRS | T2 | `cross_lang_audit` (PCWG3-integrated response, keyed multiset) |
| ADAE / ADCM / ADEX / ADLB | T3 | `cross_lang_audit` (ADAE on `USUBJID`+`AESEQ`; keyless domains by record-content multiset) · `spec_data_checks` |
| define.xml (SDTM + ADaM) | T4 | XSD 2.1 + ARM valid (`validate_xsd.sh`) · referential integrity (`validate_define.py`) · CORE parse |
| SDTM conformance | T4 | CDISC CORE run (`CORE_SDTM34_RUN_RECORD.md`) |
| ADaM conformance | T4 | Authored CORE ADaM rules via `--local-rules` (`CORE_RUN_RECORD.md`); Pinnacle 21 = authoritative for a full submission run |

Every reconciliation step writes a machine-readable status JSON and **gates the build**
(`cibuild.py`) — validation-as-code, not a manual checklist.

## 4. The single-programmer reality — stated plainly

All tracks were authored by one programmer. That removes **organizational
independence** (producer ≠ validator), which formal GxP double programming requires
and which a solo portfolio **structurally cannot demonstrate**. This is disclosed in
ADRG §6 and is not claimed away here.

What the pipeline *does* provide, proportionate to risk:

- **Methodological independence** — different languages (SAS vs R), different
  libraries (base SAS vs tidyverse vs the community-maintained `admiral`), and, at T1,
  a **third engine** whose derivation logic the author did not write (admiral's
  validated functions). A correlated single-author error must now survive *three*
  implementations to reach OS/PFS.
- **Results-level (not just dataset-level) reconciliation** — the KM medians/event
  counts that feed the efficacy claim are diffed numerically, so a dataset that
  reconciles but mis-summarises is still caught.
- **Automated gates with teeth** — reconciliation runs only count as double-programming
  evidence when the SAS engine is real (`sas_execution_mode ∈ {oda, local}`); `sim`
  mode is recorded as tautological and excluded (ADRG §6). The real-SAS gate has caught
  genuine SAS↔R divergences (e.g. the `AVALC` truncation, ADRG §6).

**Residual limitation (honest):** like all double programming, reconciliation cannot
detect a *correlated* error — if two (or three) independent tracks compute the same
wrong value, the comparison passes. Organizational independence and a second human
reviewer are the controls that would address this; they are out of scope for a
single-author portfolio and are named, not papered over.

## 5. What a full GxP build would add

A production engagement would add: a second, independent programmer for T1/T2 outputs;
an SDTM `DV` (protocol-deviation) domain to derive a discriminating per-protocol flag;
and a Pinnacle 21 submission run for the authoritative ADaM business-rule layer. None
of these change the *tiering*; they raise the independence of the highest tiers from
*methodological* to *organizational*.

## References

- ICH E9 — Statistical Principles for Clinical Trials (no double-programming mandate).
- PMC — *A risk-proportionate approach to the validation of statistical programming*.
- PHUSE / medRxiv 2025 — risk-based validation & automation-in-statistical-programming reviews.
- ADRG §6 — validation mechanics, single-author disclosure, reconciliation scope.
- `06_telemetry/ADMIRAL_RECONCILIATION.md` — the T1 third-engine track (Finding #4).
