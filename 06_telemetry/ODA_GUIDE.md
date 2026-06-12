# Maximizing SAS OnDemand for Academics (ODA) — Optimized Real-SAS Workflow

ODA is the **only** way this project obtains a *genuine* SAS production track (there is no
local SAS engine), which is what turns the cross-language reconciliation from a `sim`
tautology into real SAS↔R double-programming. This guide explains how to run it to its
fullest, fastest, and most reliably.

> **The single biggest cost is the SDTM upload**, not the SAS compute. The 34 SDTM
> `*.sas7bdat` files are ~200 MB; ODA's IOM channel runs ~1–5 MB/s, so a full upload is
> **5–15 minutes**. The SAS master driver itself runs in well under a minute. Therefore the
> whole optimization game is: *upload the SDTM once, reuse it.*

---

## 1. Prerequisites (do this before your first run)

| Requirement | Why | Check |
|---|---|---|
| **A Java runtime (JRE/JDK 8+)** | `saspy` connects to ODA over the **IOM** protocol, which is Java-based. Without a JRE you get `Unable to locate a Java Runtime`. | `java -version` must print a real version (the macOS `/usr/bin/java` stub is **not** enough — install Temurin/OpenJDK). |
| **`saspy`** | The ODA client. | `python3 -c "import saspy; print(saspy.__version__)"` |
| **Network egress to ODA** | IOM host on port **8591**. | reachable from your machine (corporate VPNs/firewalls may block it). |
| **`sascfg_personal.py`** (repo root) | `cfgname='oda'`, `iomhost`, `iomport=8591`, `authkey='oda'`. | present, not committed. |
| **`~/.authinfo`** with key `oda` | Your ODA user/password. **Permissions 600.** | `chmod 600 ~/.authinfo` |

ODA region host (this project): `odaws01-apse1.oda.sas.com` (Asia Pacific SE). ODA `$HOME`
is `/home/u64235016` and **persists across sessions** — that persistence is what makes the
upload-once strategy work.

---

## 2. The optimized run (what `cibuild.py` now does for you)

```bash
# First real run (or after a SOURCE-DATA refresh): uploads the full SDTM once.
python3 06_telemetry/cibuild.py --real-sas --force-upload-sdtm

# Every subsequent run: uploads only changed programs + the SDTM DELTA (usually nothing).
python3 06_telemetry/cibuild.py --real-sas
```

`cibuild.py` Stage 10 (`_run_saspy_stage10`) now:
0. **Connects with auto-retry** (`_oda_connect`): ODA's load-balancing object spawner
   frequently times out under load (`The load balancing object spawner timed out`). The
   connection retries with backoff (default 5 attempts, 20 s apart; tune with
   `TROPIC_ODA_RETRIES` / `TROPIC_ODA_BACKOFF`) and only proceeds once a workspace has
   actually spawned — so a transient ODA hiccup no longer fails the whole run.
   > If all retries fail, ODA itself is unavailable (peak load / maintenance); wait and
   > re-run. This is server-side, not a config or Java problem.
1. **Uploads SAS programs** every run (tiny — always ships your latest code).
2. **Syncs SDTM by delta:** lists the ODA SDTM dir and compares each file's **byte size**;
   uploads only files that are **missing or changed**. On an unchanged run this skips the
   entire ~200 MB and prints `SDTM already current on ODA — upload skipped (saved minutes).`
3. **Runs `00_master_driver.sas`** in one IOM submit (staging → SDTM map → 7 ADaM → XPT).
4. **Persists the full SAS log** to `02_production_sas/oda_master_driver.log` and surfaces
   `WARNING:`/`ERROR:` lines (fails the build on any `ERROR:`).
5. **Downloads the 7 `*_prod.xpt`** for reconciliation.

**Fail-safe guarantee:** if ODA can't be listed, or a remote size can't be read, the file is
**uploaded** — the sync never *skips on uncertainty*, so a SAS run can never execute against
stale or missing data. `--force-upload-sdtm` forces a full re-upload whenever you want
certainty (e.g., after replacing the source data cut).

---

## 3. Confirming you got a REAL run (not a sim)

After the run, check the recorded mode — this is the field that makes the "100% reconciliation"
claim meaningful:

```bash
python3 -c "import json;print(json.load(open('06_telemetry/pipeline_health.json'))['sas_execution_mode'])"
# -> 'oda'  = genuine SAS 9.4 executed on ODA this run (double-programming established)
# -> 'sim'  = byte-copy; reconciliation is tautological; NOT double-programming
```

Only `oda` (or a local `local`) result means the AESEV/ATOXGR and all other SAS derivations
were independently produced by SAS and actually reconciled cell-by-cell against the R track.

---

## 4. Other ODA helpers (already in `06_telemetry/`)

| Script | Use |
|---|---|
| `_oda_test_d_rerun.py` | Re-run the master driver after editing SAS programs **without** re-uploading SDTM (assumes it's already resident). The manual equivalent of the delta-sync. |
| `_oda_render_tfl.py` | Render the SAS production-track TFL figures on ODA (uploads programs + CbzP bridge XPTs, runs the driver + `T_tfl_generation.sas`, downloads PNGs to `09_tfl/output/sas/`). |
| `_oda_download_xpt.py` | One-shot: download the 7 `*_prod.xpt` from ODA after a driver run. |

**Further optimization available (not yet folded in):** these helpers each open their own
`SASsession`. A future improvement is a shared `oda_lib.py` (connect / sync / run / download)
so a single warm session does the driver **and** the SAS TFL render **and** the downloads —
removing repeated connection latency. The delta-sync helper above is the highest-value win
and is already in the main path.

---

## 5. Cost cheat-sheet

| Action | Cost |
|---|---|
| Full SDTM upload (200 MB @ 1–5 MB/s) | **5–15 min** — only on first run / after data refresh |
| SDTM delta (unchanged) | **seconds** (a directory listing + size checks) |
| Upload SAS programs | < 1 s |
| Master driver compute | < 1 min |
| Download 7 `*_prod.xpt` | seconds |

Net: after the one-time seed upload, a full genuine real-SAS reconciliation run is **~1–2
minutes** instead of 6–16.
