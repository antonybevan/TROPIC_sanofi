# F-042 Endpoint Approval Specification

**Specification ID:** `F042-ENDPOINT-APPROVAL-SPEC-2026-08-03`<br>
**Version:** `0.4.0`<br>
**Status:** **AUTHOR-ADOPTED FOR PATH A — PHASE 2 IMPLEMENTATION AUTHORIZED**<br>
**Parent record:** [`ENDPOINT_DECISION_RECORD_F042_T11_8_2026-08-03.md`](ENDPOINT_DECISION_RECORD_F042_T11_8_2026-08-03.md)<br>
**Execution state:** The accountable author adopted ED-01–ED-07 as written on 2026-08-04. Phase 2 may implement this specification in separate SAS and R tracks; current sealed Path A outputs remain unchanged until the full rerun, reconciliation, delayed second-pass review, and reseal pass.

## 1. Authority and interpretation boundary

This specification converts the open endpoint questions into one recommended, executable disposition. It follows the project authority hierarchy:

1. Protocol Amendment 5, 21-Jul-2008, for endpoint concepts, populations and planned analyses.
2. Corrected de Bono et al. Lancet 2010 publication for the documented correction from pain PPI nadir to baseline/reference value and the final published analysis convention.
3. Available patient-level source domains for implementation feasibility.
4. SAP v4.0 after accountable-author adoption for internal Path A programming control.

SAS/R parity and release-seal checks demonstrate reproducibility only. They do not override the protocol or corrected publication and do not create sponsor approval.

## 2. Recommended accountable-author dispositions

| Decision | Recommended disposition | Path A adoption statement |
|---|---|---|
| `ED-01` | **Adopt the rule in §3–§5** | Pain progression is cancer-related and supported by clinical and/or radiological disease evidence. Later evidence may confirm an earlier diary trigger only through its protocol-required confirming visit; later evidence must not otherwise backdate a primary event. |
| `ED-02` | **Adopt the CM+PR union in §6** | PR is staged in full, but PR is not the sole endpoint source. Direct-intent CM and PR records are both eligible. Generic radiation text is not automatically classified as palliative. |
| `ED-03` | **Adopt the sensitivity set in §7** | Primary TTPAIN/PFS includes author-adopted diary or palliative-RT criteria. Diary-only and RT-only supportive analyses isolate source contribution. |
| `ED-04` | **Adopt the SAP-native mapping in §8** | Use existing SAP identifiers `T-11-3` through `T-11-8`; do not invent an extension for the primary PSA/ORR response results. |
| `ED-05` | **Adopt ITT for TTUMOR** | TTUMOR contains one record per ITT subject. Measurable disease is the ORR population and may be a TTUMOR sensitivity/subgroup, not the primary TTUMOR denominator. |
| `ED-06` | **Adopt parameter-level origins in §9** | Efficacy TTE parameters use randomization; TTSAE uses first exposure. |
| `ED-07` | **Adopt the pain algorithm in §3–§4** | Replace the current non-conforming thresholds, summary statistic, combined-component confirmation and terminal-trigger exception. |

## 3. Pain visit construction and evaluability

### 3.1 Baseline/reference values

- Baseline is the Cycle 1 diary window: the seven expected calendar days ending on `TRTSDT`, completed before the first infusion. A complete Cycle 1 record dated on `TRTSDT` is treated as pre-infusion unless contradictory source timing is present; later visits and values outside that window do not contribute.
- Baseline PPI is the median of the non-missing `PAININT` daily values in that window.
- Baseline analgesic score is the mean of the non-missing `ANSCORE` daily values in that window.
- A baseline component is evaluable only when at least 5 distinct expected calendar dates contain a non-missing value for that component.
- Do not replace a missing baseline component with zero.
- For the analgesic percentage-change criterion, baseline mean AS must be greater than zero. Subjects with baseline mean AS equal to zero are not evaluable for the percentage-change branch unless a later controlled amendment defines a clinically justified absolute-change rule; their PPI and RT branches remain eligible.

### 3.2 Post-baseline visits

- Evaluate PPI and AS separately. A component is evaluable at a visit when at least 5 distinct expected calendar dates in its seven-day pre-evaluation window contain a non-missing value for that component. A non-evaluable companion component does not invalidate progression shown by the evaluable component.
- Visit PPI is the median of evaluable daily PPI values.
- Visit AS is the mean of evaluable daily analgesic-score values.
- Collapse exact same-test/same-date/same-value duplicates while retaining all source keys. If same-test/same-date values disagree, mark that component non-evaluable for the primary visit and route it to source review; do not select the minimum or average silently.

### 3.3 Visit/event date

1. Use the matching `SV.SVSTDTC` complete date for the scheduled evaluation visit.
2. If no complete matching SV date exists, use the maximum complete `PN.PNDTC` within the diary window and set an explicit fallback flag.
3. Do not use the minimum diary date as the visit/event date.
4. Partial or missing dates do not enter the primary exact-date analysis. Retain them for bounded sensitivity review without inventing date components.

The source profile found 1,931 exact SV matches among 1,937 PN subject-visits. The six unmatched visits therefore require the controlled fallback or a source-data review.

## 4. Pain progression algorithm

A subject has a diary-based pain progression when either component-specific criterion is met at two consecutive scheduled pain evaluations:

1. **PPI branch:** visit median PPI minus baseline/reference median PPI is at least 1 point at both visits.
2. **Analgesic branch:** `(visit mean AS - baseline mean AS) / baseline mean AS` is at least 25% at both visits, with baseline mean AS greater than zero.

Rules:

- The same component must be evaluable and qualify at both visits. A PPI trigger followed only by an AS trigger, or vice versa, is not a confirmed pair.
- The confirming assessment is the immediately next scheduled pain evaluation in protocol order and must be at least 21 calendar days after the first trigger. Treatment delays do not create an intervening visit, but an intervening scheduled pain evaluation cannot be skipped.
- An unscheduled diary assessment cannot establish or confirm the primary pair; retain it for sensitivity/adjudication.
- If the immediately next scheduled assessment is missing or non-evaluable for the triggering component, the first trigger is not confirmed. A later qualifying visit may begin a new candidate pair.
- A single trigger at the last observed visit is not confirmed and is not an event.
- For a confirmed pair, the event date is the first qualifying visit date; retain the confirming visit date and component in traceability variables.
- A qualifying direct-intent local palliative-radiotherapy record is a standalone pain-progression criterion and uses its complete treatment/procedure start date. It does not require a second diary visit.

This replaces the current `PPI >=2`, absolute `AS >=10`, median-AS, combined-component and terminal-trigger rules.

## 5. Cancer-related supporting disease evidence

Pain progression is eligible for TTPAIN and as the pain component of PFS only when it is cancer-related. The primary source set accepts:

- **Radiological evidence:** LS-derived RECIST `ADRS.OVRLRESP='PD'`, including unequivocal non-target progression or a new lesion, with a complete assessment date no later than the diary confirming visit. A DS milestone injected into `OVRLRESP` is not radiological evidence and must remain source-distinguishable. The post-2010 demonstration `BSGRESP` rule is not primary trial-era supporting evidence.
- **Clinical evidence:** `DS.DSDECOD` equal to `DISEASE PROGRESSION` or `PROGRESSION`. When only `DSSTWK` is available, set the reconstructed point date to `RANDDT + 7 × (DSSTWK - 1)` days and represent the week uncertainty as point date `-3.5` through `+3.5` days. For the primary derivation, conservatively require the point date plus 4 calendar days to be no later than the diary confirming visit. Boundary-ambiguous records go to sensitivity/adjudication.
- **Treatment evidence:** a direct-intent local palliative/antalgic radiotherapy record for a cancer site under §6.

PSA progression remains an independent PFS component and must not, by itself, be used to relabel an otherwise unsupported pain trigger as clinically/radiologically supported pain progression.

For diary progression, supporting evidence may be present on or before the first trigger or may arise by the confirming visit. Evidence after the confirming visit does not backdate the primary pain event. Unsupported diary triggers are retained in an adjudication dataset but are censored/non-events in the primary TTPAIN and PFS derivations.

## 6. CM and PR source handling

### 6.1 Ingestion

- Stage the full PR domain; do not filter at ingestion.
- Preserve the already staged full CM domain and its supplemental qualifiers.
- Preserve source text, keys, date precision and domain provenance.

### 6.2 Direct-intent classification

A record is an automatic palliative-RT candidate only when:

1. the treatment/procedure text represents radiation/radiotherapy; and
2. the same source text explicitly contains `PALLIATIVE` or `ANTALGIC`.

Generic `RADIOTHERAPY`, prior-radiation categories, radiopharmaceuticals and text matches such as estradiol are not automatically palliative pain events.

### 6.3 Cross-domain precedence

- Use the union of direct-intent CM and PR candidates.
- Exact subject/date duplicates may be collapsed to one clinical event while retaining both source records and provenance.
- For an exact duplicate, a complete PR procedure start date is the displayed event date and CM is corroborative.
- Non-exact dates are not silently merged. Retain both candidates for adjudication or apply a subsequently adopted same-course matching rule.
- A missing or partial start date is excluded from the primary exact-date event derivation and included only in bounded sensitivity/adjudication evidence.

Observed direct-intent inventory:

| Source | Rows | Subjects | Complete start dates | Post-randomization complete dates |
|---|---:|---:|---:|---:|
| CM (`PALLIATIVE` or `ANTALGIC` radiotherapy text) | 13 | 10 | 12 | 12 |
| PR (`PALLIATIVE` or `ANTALGIC` radiotherapy text) | 3 | 1 | 3 | 3 |

The direct-intent CM and PR subject sets do not overlap. This is why PR-only precedence is not acceptable.

## 7. Required sensitivity and supporting analyses

1. **Primary:** author-adopted diary progression or direct-intent palliative RT, with cancer-related qualification in §5.
2. **Diary-only sensitivity:** remove RT-only events; retain qualified diary events.
3. **RT-only supportive analysis:** treat only direct-intent, complete-date palliative/antalgic RT as events; present counts, dates, KM summaries where estimable and a subject-level lineage listing for QC.
4. **Date-bound sensitivity:** separately disposition partial/missing RT dates; do not impute them into the primary result.
5. **Population support:** present TTUMOR measurable-disease subgroup/sensitivity while retaining ITT as primary.

Every analysis must report event-source counts and subject-level before/after reclassification relative to the currently sealed Path A output.

The provisional local worksheet fields for RT adjudication and the
current-versus-provisional subject comparison are defined in the [F-042 CM/PR
adjudication worksheet specification](F042_ADJUDICATION_WORKSHEET_SPEC_2026-08-03.md).

## 8. TFL identifier mapping

| ID | Required SAP output |
|---|---|
| `T-11-3` | PSA Response Rate |
| `T-11-4` | ORR per RECIST v1.0 |
| `T-11-5` | Pain Response Rate |
| `T-11-6` | Time to Tumour Progression |
| `T-11-7` | Time to PSA Progression |
| `T-11-8` | Time to Pain Progression |

`T-11-8b` may remain an explicitly author-adopted ORR denominator sensitivity for Path A, but it must not replace or rename any primary SAP identifier.

## 9. Populations and time origins

| Parameter | Primary population | Start date |
|---|---|---|
| OS | ITT | `RANDDT` |
| PFS | ITT | `RANDDT` |
| TTPSA | ITT | `RANDDT` |
| TTUMOR | ITT | `RANDDT` |
| TTPAIN | ITT, subject to endpoint evaluability/qualification | `RANDDT` |
| TTSAE | Safety | `TRTSDT` |

ORR remains restricted to ITT subjects with measurable disease. TTUMOR must not inherit the ORR denominator.

## 10. Implementation acceptance criteria after author adoption

- SAS and R implementations use the same author-adopted rule but are programmed separately without copying derivation code between languages.
- Regression fixtures cover baseline AS zero, same-day Cycle 1 values, component-specific 5-of-7 evaluability, exact and discordant same-day duplicates, an interval below 21 days, an immediately consecutive qualifying assessment, an intervening missing/non-evaluable scheduled assessment, alternating PPI/AS triggers, terminal single trigger, unscheduled diaries, RT-only event, exact CM/PR duplicate, non-exact cross-domain records, missing RT start date, DS week-date boundary uncertainty and SV-date fallback. A DS week-offset fixture qualifies for the primary cancer-related rule only when `point date + 4 days <= confirming visit date`.
- Every currently labelled pain-led PFS record has a before/after disposition and source lineage.
- TTUMOR contains the full ITT denominator and a measurable-disease supportive result.
- TFL catalog, physical output labels, ARM/ARS, Define methods, ADRG and traceability use the §8 mapping.
- A delayed second-pass author review uses a frozen checklist and is recorded separately from initial programming.
- Full real-SAS DAG, separate R reconciliation, relevant scoped admiral checks, automated output QC and release verification pass before reseal.
- No document may describe the result as independently reviewed, sponsor-approved, medically approved, SAP-approved for filing, or filing-ready. External qualified review and sponsor governance remain required for regulated reuse.

## 11. Accountable-author election

The accountable author must select one in the parent decision record:

- [x] **ADOPT AS WRITTEN FOR PATH A** — authorize implementation of §§3–10 for the controlled non-submission demonstration. Antony Bevan, 2026-08-04; the parent decision record is authoritative.
- [ ] **ADOPT WITH DOCUMENTED MODIFICATIONS FOR PATH A** — attach exact replacement wording; no verbal-only change is executable.
- [ ] **REJECT / RETURN FOR REVISION** — state the rejected decision IDs and rationale.

Blank boxes and blank accountable-author fields mean no decision and no authorization to implement.
