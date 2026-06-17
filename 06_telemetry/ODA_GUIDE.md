# Maximizing SAS OnDemand for Academics (ODA) — Resilient Real-SAS Workflow

ODA is the **only** way this project obtains a *genuine* SAS production track (there is no local
SAS engine), which is what turns the cross-language reconciliation from a `sim` tautology into
real SAS↔R double-programming. This guide explains the resilience architecture and how to run it.

> **Two costs dominate, and both are now handled:** (1) the ~200 MB SDTM upload (IOM ~1–5 MB/s =
> 5–15 min) — done **once** via the idempotent seed job; (2) ODA's flaky **object spawner**, which
> times out under load — absorbed by the **connection broker** (status-gated jittered backoff).

---

## 1. Prerequisites

| Requirement | Why | Check |
|---|---|---|
| **A Java runtime (JRE/JDK 8+)** | `saspy` connects over IOM (Java). | `java -version` prints a real version (the macOS `/usr/bin/java` stub is not enough). |
| **`saspy`** | ODA client. | `python3 -c "import saspy"` |
| **Network to ODA** | IOM on port **8591** to your region's `odaws*.oda.sas.com`. | reachable (VPN/firewall may block). |
| **`sascfg_personal.py`** + **`~/.authinfo` (key `oda`, perm 600)** | connection + credentials. | present, not committed. |

**Spawner failover (important).** saspy ignores `iomhost`/`iomport` passed at `SASsession()`
call time for an ODA config ("ignored due to configuration restriction"), so failover across a
region's workspace servers must be set as an **iomhost list in `sascfg_personal.py`**:

```python
'iomhost': ['odaws01-apse1.oda.sas.com', 'odaws02-apse1.oda.sas.com'],  # your region's servers
```

saspy then fails over across them itself. The broker reads the region from the cfg for telemetry
labelling; it does not (and cannot) inject the host list at call time. Region server sets are
listed in `oda_broker.py` (`REGION_HOSTS`). If *all* servers in your region time out across many
attempts (as distinct from one server), that indicates an ODA-side capacity/throttle condition,
not a config problem — wait for an off-peak window rather than continuing to retry.

---

## 2. The two jobs

### Job A — seed the SDTM (idempotent; run once, or after a data refresh)
```bash
python3 06_telemetry/seed_sdtm.py            # uploads only if the ODA manifest mismatches local
python3 06_telemetry/seed_sdtm.py --force    # override: re-upload regardless
```
`seed_sdtm.py` computes a per-dataset `sha256`/`nrows` **manifest**, and:
- if the ODA library already matches → **zero upload**, exit 0;
- else uploads, **re-reads row counts back from ODA** to catch a half-upload, then writes the
  manifest sentinel **last** (transactional — a partial upload leaves no valid manifest).

### Job B — reconcile (on demand; assumes SDTM resident)
```bash
python3 06_telemetry/cibuild.py --real-sas
```
`cibuild.py` Stage 11:
1. **Connects via the broker** (§3) — rides transient spawner timeouts.
2. **Verifies** the SDTM manifest on ODA. If it is missing/stale, the run **fails with a clear
   message to run Job A** — it never silently drops to sim against an unseeded library.
3. Runs `00_master_driver.sas`, captures the log to `02_production_sas/oda_master_driver.log`,
   downloads the 7 `*_prod.xpt`, and reconciles them against the R `*_v.xpt`.

> `cibuild.py --real-sas --force-upload-sdtm` bundles a forced Job-A seed into the same session.

---

## 3. The connection broker (`oda_broker.py`)

Replaces blind retries with a resilient state machine:
- **Status-gated, full-jitter exponential backoff** within a wall-clock budget (no fixed loop).
  Tune with `TROPIC_ODA_MAX_WAIT` (seconds; default 3600). `TROPIC_ODA_RETRIES` still works as a
  back-compat alias (`retries × ~60 s`).
- **Error taxonomy** — `AUTH` and `CONFIG_ENCRYPTION` **fail fast** (fix and re-run, no budget
  burned); `CLUSTER_UNAVAILABLE` / `SPAWN_FAILED` / `SESSION_LIMIT` / `NETWORK` retry with
  class-specific cooldowns; an unhealthy `status.oda.sas.com` defers the attempt.
- **Slot hygiene** — a single-flight file lock prevents concurrent spawns, a startup sweep +
  cooldown handles a prior crash's orphaned slot, and every session path tears down in `finally`.
- **Live probe earns the mode** — before returning, the broker submits a runtime **nonce** and
  confirms it echoes back from the workspace. A cached/dead session cannot echo a fresh nonce, so
  `sas_execution_mode='oda'` is **earned, never asserted** from a bare connection.
- **Attempt ledger** (`oda_status.json`, jsonl) feeds `recommend_window()`, which returns your
  empirically best connect window after a day of data — schedule Job A into it.

---

## 4. Confirming a GENUINE run (the health contract)

`06_telemetry/pipeline_health.json` records exactly what happened:

```json
// genuine ODA double-programming:
{ "sas_execution_mode": "oda", "oda_endpoint": "odaws03-usw2.oda.sas.com",
  "oda_attempts": 4, "oda_total_wait_s": 312, "sdtm_manifest_sha": "…",
  "probe_nonce_echoed": true, "reconciliation": "SAS_vs_R", "reconciliation_status": "PASS" }

// ODA unreachable this window -> honest sim (never relabeled as oda):
{ "sas_execution_mode": "sim", "oda_last_error_class": "CLUSTER_UNAVAILABLE",
  "oda_attempts": 37, "next_recommended_window": "14:00-17:00 (local)",
  "reconciliation": "sim_only" }
```

Genuine double-programming = `sas_execution_mode == 'oda'` **and** `reconciliation == 'SAS_vs_R'`.
A `sim` / `sim_only` result is honestly labeled and is **not** evidence of SAS↔R parity.

---

## 5. Cost cheat-sheet

| Action | Cost |
|---|---|
| Job A first seed (200 MB @ 1–5 MB/s) | 5–15 min, **once** |
| Job A when already resident | seconds (manifest match → zero upload) |
| Broker connect (ODA healthy) | seconds–minutes (rides spawner timeouts) |
| Job B master driver + download | < 1–2 min |

After the one-time seed, a genuine real-SAS reconciliation run is **~1–2 minutes** whenever ODA's
spawner is responsive.
