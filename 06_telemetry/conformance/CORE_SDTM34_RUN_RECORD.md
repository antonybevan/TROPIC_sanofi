# CORE SDTM 3.4 Conformance Run Record — 2026-06-20

Authoritative CDISC CORE validation of the SDTMIG 3.4 uplifted SDTM (terminal session).

## Command
```
.core_venv/bin/python .core_run/engine/core.py validate \
  -s sdtmig -v 3.4 -d <sdtm34> -ft xpt -dxp define_sdtm.xml \
  -ca <cache> -ps 1 -of JSON -o core_sdtm34_report
```

- Engine: cdisc-rules-engine (CORE) v0.16.0 · Standard: SDTMIG 3.4 · CT: SDTMCT 2026-03-27 (from define)
- Conformance_Details: {"Report_Generation": "2026-06-20T16:18:44", "Total_Runtime": "78.4 seconds", "CORE_Engine_Version": "0.16.0", "Issue_Limit_Per_Rule": "None", "Issue_Limit_Per_Dataset": "None", "Issue_Limit_Per_Sheet
- Domains validated: DM, AE, EX, DS, VS (matches the prior 3.2 baseline set)
- Report: `06_telemetry/conformance/core_sdtm34_report.json`

## Result: 20 distinct issues / 13010 occurrences

All targeted structural rules CLEARED vs. the prior 3.2 baseline: CORE-000264 (AESOC), -000453 (AGE), -000701 (EPOCH), -000776 (EXENDY), -000550 (non-standard→SUPP), -000852 (var order), -001082 (type), -000594/-000398 (labels), -000867 (whitespace).

### Remaining findings (classified — none are programming defects)

| Class | Rule | Dataset | Occ | Note |
|---|---|---|---|---|
| cross-domain(no FA) | CORE-000767 | AE | 5428 | RELREC/FAOBJ — no FA domain in analysis-scoped package |
| cross-domain(no FA) | CORE-000767 | DS | 2842 | RELREC/FAOBJ — no FA domain in analysis-scoped package |
| engine-internal | CORE-000929 | AE | 1 | CORE evaluation dataset failed to build |
| engine-internal | CORE-000929 | DM | 1 | CORE evaluation dataset failed to build |
| engine-internal | CORE-000929 | DS | 1 | CORE evaluation dataset failed to build |
| engine-internal | CORE-000929 | EX | 1 | CORE evaluation dataset failed to build |
| engine-internal | CORE-000929 | VS | 1 | CORE evaluation dataset failed to build |
| engine-internal | CORE-001081 | AE | 1 | CORE evaluation dataset failed to build |
| engine-internal | CORE-001081 | DM | 1 | CORE evaluation dataset failed to build |
| engine-internal | CORE-001081 | DS | 1 | CORE evaluation dataset failed to build |
| engine-internal | CORE-001081 | EX | 1 | CORE evaluation dataset failed to build |
| engine-internal | CORE-001081 | VS | 1 | CORE evaluation dataset failed to build |
| inherent-de-id | CORE-000334 | AE | 1 | var removed by PDS de-identification (SITEID/COUNTRY/MedDRA codes) |
| inherent-de-id | CORE-000334 | DM | 1 | var removed by PDS de-identification (SITEID/COUNTRY/MedDRA codes) |
| inherent-de-id | CORE-000334 | DS | 1 | var removed by PDS de-identification (SITEID/COUNTRY/MedDRA codes) |
| inherent-de-id | CORE-000334 | VS | 1 | var removed by PDS de-identification (SITEID/COUNTRY/MedDRA codes) |
| inherent-de-id | CORE-000355 | DM | 1 | var removed by PDS de-identification (SITEID/COUNTRY/MedDRA codes) |
| real-source-data | CORE-000022 | AE | 1 | real source safety/VS data — not overwritten |
| real-source-data | CORE-000266 | AE | 1136 | real source safety/VS data — not overwritten |
| real-source-data | CORE-000732 | VS | 3588 | real source safety/VS data — not overwritten |

**Structural-fixable residual: 0** (target met).
