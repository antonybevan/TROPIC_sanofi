# TROPIC Release Note — `v0.1.0-demo-rc.1`

**Product:** Controlled clinical-programming **demonstration** pipeline  
**Study:** EFC6193 / XRP6258 (TROPIC, NCT00417079)  
**Tag:** `v0.1.0-demo-rc.1`  
**Seal date:** 2026-07-09  
**Git tip at tag:** `git rev-parse v0.1.0-demo-rc.1^{commit}` (annotated tag on this branch tip)  
**Seal artifact commits:** `f7bfb48` → `29d8016` → `647095c`

---

## One-line verdict

**Release-candidate PASS** for a **controlled non-submission demo** package — full ODA dual-language DAG, hash-sealed run record, dispositioned findings — **not** an FDA filing package and **not** Part 11.

---

## What “PASS” means here

| Claim | Bound? |
|---|---|
| Full 30-stage DAG executed this seal generation cycle under real SAS (`oda`) | Yes |
| SAS↔R dataset + results reconciliation non-simulated PASS | Yes |
| Third-engine admiral core (ADSL, OS, PFS) in-DAG PASS | Yes |
| Controlled TFL catalog complete (18 in-scope; 21 SAP IDs deferred with reasons) | Yes |
| Validation strategy + log cleanliness + metadata control PASS | Yes |
| Release-run hash seal + RC checklist 16/16 | Yes |
| Active CONFIRMED Critical/Major findings | None (RESOLVED or ACCEPTED) |
| Sponsor-approved SAP / real CbzP IPD / Part 11 / commercial P21 clearance | **No** |

---

## Evidence anchors (read these first)

| Artifact | Role |
|---|---|
| `06_telemetry/pipeline_health.json` | Run telemetry: `schema_version=run_scope_v1`, `GREEN`, `oda`, `full_dag`, 30/30 PASS |
| `06_telemetry/release_run_manifest/release_run_manifest.json` | Hash seal: `PASS`, `evidence_grade=release_candidate`, seal `c01e744fe5ba3a1e70fbe4a0b4304da1a8f211edb21cc5ba76f85db3f6ed0201` |
| `docs/RELEASE_RUN_MANIFEST.md` | Human-readable seal summary |
| `06_telemetry/release_candidate/release_candidate_status.json` | RC go/no-go: `PASS`, 16 checks, 0 blockers |
| `docs/RELEASE_CANDIDATE_CHECKLIST.md` | Reviewer checklist |
| `tfl_output_catalog.yaml` | Controlled output universe (in-scope vs deferred) |
| `audit/FINDINGS_DISPOSITION_BOARD.md` | Crit/Major disposition classes and honesty boundary |
| `audit/findings_register.csv` | Machine register (ACCEPTED/RESOLVED) |
| `validation_strategy.yaml` + `docs/VALIDATION_STRATEGY_CONTROL_REPORT.md` | Risk-based validation control |
| `08_reviewers_guides/ADRG.md` / `SDRG.md` / `BDRG.md` | Reviewer explanation layer |

---

## Run identity (this seal)

```text
sas_execution_mode:     oda
pipeline_health_status: GREEN
schema_version:         run_scope_v1
run_scope:              full_dag
stages:                 30 expected / 30 recorded / 0 NOT_RUN
provenance_guard:       passed (prod vs val byte-distinct)
reconciliation:         SAS_vs_R PASS (non-simulated)
admiral:                in-DAG PASS (ADSL, OS, PFS scoped core)
worktree at seal:       clean
```

---

## Honesty boundary (must not be omitted)

1. **CbzP arm** is synthetic/reconstructed (Guyot OS/PFS; PH-scaled secondaries). Comparative TFLs are **non-confirmatory**.
2. **Real patient SDTM (MP)** and ODA credentials are **not** in git; bare clone cannot re-run the real pipeline.
3. **eCTD** uses **EXAMPLE** application identifiers and is a structure/demo package, not a real submission sequence.
4. **SAP v4.0** is remediation authority (lock memo PASS for programming; FAIL as sponsor-approved submission SAP).
5. **Part 11:** hash seals and Git history are **not** a validated system / e-signature claim.
6. **P21 commercial ADaM** rule pack is not claimed; local CORE + dual-lang + admiral substitute.
7. **Controlled TFL scope** is 18 IDs; 21 SAP full-catalog IDs remain **deferred** with explicit reasons.

---

## What changed in this release train

- Manifest-driven 30-stage DAG including **admiral** third engine (gated).
- **TFL catalog control** (`tfl_output_catalog.yaml`) + index gate.
- **Findings disposition board** → no active CONFIRMED Crit/Major for RC gate.
- Delivery controls: evidence layers, validation strategy, log cleanliness, release-run seal, RC checklist.
- Full **ODA** proof run sealed as `full_dag` with `schema_version=run_scope_v1`.

---

## How a reviewer should re-check (no patient data required for structure)

```bash
# Machine seals (local clone with artifacts)
python3 -c "import json; print(json.load(open('06_telemetry/release_run_manifest/release_run_manifest.json'))['status'])"
python3 -c "import json; print(json.load(open('06_telemetry/release_candidate/release_candidate_status.json'))['status'])"
python3 -c "import json; h=json.load(open('06_telemetry/pipeline_health.json')); print(h['schema_version'], h['run_scope'], h['sas_execution_mode'], h['pipeline_health_status'])"

# Demo smoke (no SDTM / no SAS)
python3 06_telemetry/cibuild.py --demo
```

Full real re-run requires licensed SDTM placement + ODA/local SAS (see `REPRODUCIBILITY.md`).

---

## Tag (repository)

```text
git tag -a v0.1.0-demo-rc.1   # points at this note commit (cff7aa1)
```

Machine seal artifacts were landed at `f7bfb48`; this tag includes the reviewer narrative on top of that sealed tip.

---

## Recommended next steps (optional)

1. Push tag when remote share is intended: `git push origin main --tags` (only with explicit approval).
2. Snapshot immutable ODA evidence under `06_telemetry/evidence/` if a frozen offline pack is required.
3. Reviewer package pass: ADRG/SDRG cross-links to this release note and disposition board.
4. Do **not** describe this tag as submission-ready without new Crit/Major board + sponsor data + Part 11 program.
