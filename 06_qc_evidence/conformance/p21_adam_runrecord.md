# Pinnacle 21 Community ADaM Validation Run Record

**Record ID:** TROPIC-P21-ADAM-2026-08-12-04
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
| Inputs | Seven exact current MP-arm production XPT payloads: ADAE, ADCM, ADEX, ADLB, ADRS, ADSL, ADTTE |
| Filename staging | Byte-identical copies were presented as the submission filenames `adae.xpt` through `adtte.xpt`; local `_prod` engineering suffixes were removed without content transformation |
| Scope | 121,320 records; 7 of 7 datasets processed; 0 rejected datasets |
| Rule catalog | 388 distinct rules listed in the workbook |
| Result | 30 issue-summary groups; 2,373 aggregate occurrences |
| Process result | Report generated and client logged `Validation: Process completed`; shell exit code `5` retained with the installation-compatibility condition |
| Raw report | `pinnacle21-report-2026-08-12T16-58-controlled-exact-byte-final.xlsx`; SHA-256 `8184a5ccedca45ccd25c444cc3aca350798085a26d03153dfbb122da9c217024` |
| Aggregate QC | Workbook ZIP integrity passed; independent artifact-tool and openpyxl reads reconciled 7 datasets, 121,320 records, 0 rejects, 388 rules, 30 issue groups, and 2,373 occurrences |
| Pipeline binding | GREEN full DAG; 37/37 stages PASS; SAS execution mode `oda`; health timestamp `2026-08-12T10:28:13.216075+00:00`; source-tree SHA-256 `25eea11519389347cf943ecdb2c57c55733c32f781241f158d91acca35eb6fa5` |

The raw workbook is retained outside Git as vendor-licensed runtime output under the repository's controlled-artifact policy; it also embeds local execution paths. The `Details` sheet in this aggregate-only run is header-only. This record and `p21_adam_summary.json` retain the run identity, cryptographic bindings, aggregate counts, and dispositions needed for repository review.

This superseding run validates the exact seven XPT byte sequences produced by the bound GREEN run at `2026-08-12T10:28:13.216075+00:00`. No header-only equivalence inference is used. The standard-named validator inputs were byte-identical staging copies of the current `_prod.xpt` artifacts, and their SHA-256 values were checked before and after staging.

An exploratory invocation supplied the local engineering filenames (`*_prod.xpt`) directly and caused Community to classify the sources as nonstandard domains such as `ADAE_PROD`, producing a misleading global reject and missing-dataset messages. It is not the controlled result. The final invocation used standard submission filenames, matching the Module 5 delivery contract. `platform/stage_p21_adam_inputs.py` now makes that filename-only staging step explicit, byte-verifies it, checks each internal XPT member name, and fails closed on a reused destination.

## Input hash binding

| Dataset | Records | SHA-256 |
|---|---:|---|
| ADAE | 5,428 | `fcad58d6706ecfc8cd4508f874fcdd343a1f42588686edc4932ca8edaaab2a93` |
| ADCM | 24,534 | `87a5c0c51f139c9fc18eeb01612bf413d159c9d71b638233155944d06637a6d0` |
| ADEX | 7,820 | `88f48e9a46775ef5b9e8d40395c277badde3ebdc83fee153fea6e7793c28240d` |
| ADLB | 78,619 | `e2e11cfc900be0129ef5e6d6dfeeabbd36b04bec57be5353eaa1165fb7bf10cd` |
| ADRS | 2,322 | `2355507061b1c37743cd0d543ff2bb129ddbbc33d48e74f755dad711bbd4ab4f` |
| ADSL | 371 | `b4f465cc39e4a90706c72bde69cc21b56f5aab11506f25af1190d0e9b96459ad` |
| ADTTE | 2,226 | `377e13bf3b34524692b48ed77f56df1beec8b5b972c7015cf09220c530173840` |

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
