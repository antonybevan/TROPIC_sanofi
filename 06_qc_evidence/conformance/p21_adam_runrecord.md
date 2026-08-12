# Pinnacle 21 Community ADaM Validation Run Record

**Record ID:** TROPIC-P21-ADAM-2026-08-12-02  
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
| Rule catalog | 387 listed rules; 5,546 checks reported by the Community run summary |
| Result | 30 issue-summary groups; 2,373 aggregate occurrences |
| Process result | Report generated and client logged `Validation: Process completed`; shell exit code `5` retained with the installation-compatibility condition |
| Raw report | `pinnacle21-report-2026-08-12T14-05-definitive.xlsx`; SHA-256 `94d29012c0b5cdfa90bab6f4b1a335a65de3674364ace14cc4b9a50be5f16629` |

The raw workbook is retained outside Git because its details sheet includes record-level identifiers. This record and `p21_adam_summary.json` retain only run identity, hashes, aggregate counts, and dispositions.

## Input hash binding

| Dataset | Records | SHA-256 |
|---|---:|---|
| ADAE | 5,428 | `7d69bfd565d09305802058e8d5708642ae2872ff8939eac60924e8d742af6694` |
| ADCM | 24,534 | `ee86a5e4ac69b22ed8d19aa5cf35b28f52caaf36f6242a5faf7a576e02c0f593` |
| ADEX | 7,820 | `4492a011592c763429cdb84a87e80eb1c04ca2731c7eedfbbabd3175878c9e7e` |
| ADLB | 78,619 | `e143726865d89ec58afea959311d0089afd340e12392be70250d23d45d6030be` |
| ADRS | 2,322 | `36b1e6aaf868e2243fb3f97f68bf1982180124cc9cfe8a8d070568e024c73a87` |
| ADSL | 371 | `41bd2a3fa78b6750d6059f40cfd6293cd158db7ec99915f3908d244ff39c92ac` |
| ADTTE | 2,226 | `597ffd31e266f4fda44dfc6f82f37532cad00987838445c3b5deb9f92f86fec5` |

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
