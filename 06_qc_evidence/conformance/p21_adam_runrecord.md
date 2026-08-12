# Pinnacle 21 Community ADaM Validation Run Record

**Record ID:** TROPIC-P21-ADAM-2026-08-12-03
**Execution date:** 2026-08-12
**Status:** `EXECUTED_WITH_OPEN_FINDINGS_AND_COMPATIBILITY_CAVEAT`
**Use:** `INFORMATIVE_ONLY`
**Licensed Enterprise execution:** `NOT_EXECUTED`

## Controlled execution

| Item | Recorded value |
|---|---|
| Application | Pinnacle 21 Community 4.1.0, build 4.1.0.4652 |
| Distribution verification | Apple-notarized Developer ID Application: Pinnacle 21 LLC (`56C9Z22DN3`); stapled notarization ticket |
| Client component | `p21-client-1.0.8.jar`; SHA-256 `1d6cb1c03c16bb7dec2c2e04933fc1dcd01bcad8781c456000434cee0173e8b7` |
| Invocation | Vendor-documented Community CLI path, using the Java 8 runtime bundled with the installed application |
| Validation engine | FDA 2508.1 |
| Configuration | ADaM-IG 1.3 (FDA); SHA-256 `7076c498f841346dac1fe48afb6ef480ce22e8a42a02aeb07453f751a8b9f014` |
| Controlled terminology | ADaM CT 2024-03-29 (`4ea8d18df997f0ed4c7bc41e3aeba8379fbe388ef3026c9d03122256036bf8ab`); SDTM CT 2024-03-29 (`973f55002840116158fa79fb89361a174998908404e8e6ef7b7de3e59543d1ce`) |
| Define-XML | Define-XML 2.1 explicitly declared; `03_metadata/define/define.xml`; SHA-256 `74256966d9247f117ffba4a52712733bd42abc11f5aca5061aa73e210e7db204` |
| Inputs | Seven final MP-arm production XPTs: ADAE, ADCM, ADEX, ADLB, ADRS, ADSL, ADTTE |
| Scope | 121,320 records; 7 of 7 datasets processed; 0 rejected datasets |
| Rule catalog | 388 distinct rules listed in the workbook |
| Result | 30 issue-summary groups; 2,373 aggregate occurrences |
| Process result | Report generated and client logged `Validation: Process completed`; shell exit code `5` retained with the installation-compatibility condition |
| Raw report | `pinnacle21-report-2026-08-12T15-02-final-green.xlsx`; SHA-256 `2cb4cc952939d5ca4681197a09ff256abc5e9a87c9839296cca82195deba4f9f` |
| Pipeline binding | GREEN full DAG; 37/37 stages PASS; SAS execution mode `oda`; health timestamp `2026-08-12T09:29:59.539074+00:00`; source-tree SHA-256 `81dadd3c02bf521bf11fce32f67f30ec4c70913059675cc576c895b8182a605d` |

The raw workbook is retained outside Git because its details sheet includes record-level identifiers. This record and `p21_adam_summary.json` retain only run identity, hashes, aggregate counts, and dispositions.

## Input hash binding

| Dataset | Records | SHA-256 |
|---|---:|---|
| ADAE | 5,428 | `0ed941880c91ce8ce94a751e6acb91306a241bf6ce864e7f97b09488c421c4dc` |
| ADCM | 24,534 | `42efe96796572e0044450ea1f838efbc7884d8f453dd5b09694a40b5041618c9` |
| ADEX | 7,820 | `1cac2fcf52782f01adefb8df890064017b96fb64171ad00ff23e6361e02bd377` |
| ADLB | 78,619 | `71f0d7f016b81209372a38529355e129736dbed2c31781b12dc9b5335f95edc5` |
| ADRS | 2,322 | `2bb24d70cff299b755a70c94c2d46874679b5ca73045d6f3fbef2591a3a3640e` |
| ADSL | 371 | `ff0232e2d7358ac4a9cf2d607802a9a3d9c342d48928e28d2fbe1d7941b62c91` |
| ADTTE | 2,226 | `e53d06e57d74ea148a93ae5425a7ac551e9732db12b41539e4ff5385f9a5e8b1` |

## Before/after remediation

| Measure | Initial run | Definitive post-rebuild run | Change |
|---|---:|---:|---:|
| Issue-summary groups | 37 | 30 | −7 |
| Aggregate occurrences | 86,611 | 2,373 | −84,238 (−97.3%) |
| Dataset rejects | 0 | 0 | no change |

The seven eliminated groups were the flag findings caused by nonconforming `N` values in one-sided ADaM flags. Paired SAS/R programs, the specification, Define-XML, and generated data now use `Y`/null for ADAE/ADCM `TRTEMFL`, ADLB `ANL01FL`, and standard ADLB `ABLFL`. The nonstandard ADLB `BASEFL` variable was removed.

## Residual disposition

| Finding family | Occurrences | Disposition |
|---|---:|---|
| ADaM-only traceability context (`AD1024/25/26`) | 3 | Expected for this scoped run. Supplying the transformed public SDTM package creates identifier-traceability noise; a regulated final run requires the locked sponsor source context. |
| Source timing (`AD0099`, `AD0361`, `AD0046`) | 1,604 | Six reversed ADAE intervals and day-zero source-relative-day values remain. No silent clinical-data correction is allowed without an approved source-query or derivation rule. |
| Controlled terminology (`CT2001`) | 124 | Public-source action terms require a governed source-to-CT mapping decision; not silently recoded. |
| Numeric/character paired representations (`AD0150`, `AD0149B`) | 587 | Includes numeric values paired with display/category text or rounded character values. Requires parameter-level metadata/model review before any regulated reuse. |
| Standard labels/types/required variables (`AD0018`, `AD0047`, `AD0200`, `AD0320`) | 36 | Open standards backlog. Some items are sponsor-defined extensions or physical-versus-semantic datatype differences; all require approved specification/Define disposition. |
| Define/dataset type messages (`SD0059`) | 19 | Define-XML uses semantic date datatypes while XPT stores numeric SAS dates. Retained for qualified standards review; not changed solely to suppress Community output. |

No residual is represented as “clean,” “accepted by FDA,” or independently approved. The detailed aggregate inventory is in `p21_adam_summary.json`.

## Compatibility caveat

The installed, notarized Community 4.1.0 application and its bundled `p21-client-1.0.8.jar` completed the run with the current downloaded FDA 2508.1 engine. The generated Validation Summary nevertheless reports **`Incompatible CLI used`**. The warning persisted when the JAR was copied to the vendor-documented writable Community directory and Define-XML 2.1 was declared explicitly.

Accordingly:

- the run is genuine issue-discovery evidence, not a placeholder;
- the process-completed message and zero rejects do not convert findings into a pass;
- severity rendering and issue classification are not treated as authoritative;
- Community is not licensed Pinnacle 21 Enterprise; and
- the report is not submission-clearance or regulatory-acceptance evidence.

## Qualification decision

- `PINNACLE21_COMMUNITY=INFORMATIVE_ONLY`
- `LICENSED_PINNACLE21_ENTERPRISE=NOT_EXECUTED`
- `SUBMISSION_CLEARANCE=NOT_CLAIMED`

The regulated-use closure path is defined in `docs/QUALITY_SYSTEM_BOUNDARY.md`.
