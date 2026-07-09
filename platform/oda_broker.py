"""
oda_broker.py — governed helper for connecting to SAS OnDemand for Academics (ODA).

ODA's load-balancing object spawner intermittently times out under load (free, oversubscribed
tier). A naive retry loop hammers the cluster and orphans workspace-session slots. This broker
replaces blind retries with:

  * status-gated, full-jitter exponential backoff (never a fixed blind loop);
  * an error taxonomy that fails fast on AUTH / CONFIG_ENCRYPTION and only retries the
    transient classes within a wall-clock budget;
  * slot hygiene — single-flight file lock + startup orphan sweep + explicit/context teardown;
  * a LIVE round-trip probe: 'oda' mode is *earned* by echoing a runtime nonce, never asserted
    from a bare connection;
  * an append-only attempt ledger (oda_status.json) feeding recommend_window().

Everything that touches the outside world (saspy session, status page, sleep, clock, lock) is
injectable, so the state machine is unit-testable without Java, network, or a live ODA.

Public API:
    connect(max_wait_s=3600, ...) -> OdaConnection      # raise OdaFatal / OdaExhausted
    submit_timed(sas, code, timeout_s=1800) -> dict      # raise OdaExecTimeout
    classify(exc_text) -> str
    teardown(sas, force=False)
    recommend_window() -> str | None
    detect_region_hosts() -> (region, [fqdn, ...])
"""
import os
import json
import time
import signal
import random
import datetime
import shutil
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(HERE, ".."))
CFG_FILE = os.path.join(PROJECT_ROOT, "sascfg_personal.py")
LEDGER = os.path.join(HERE, "oda_status.json")
LOCKFILE = os.path.join(HERE, ".oda_singleflight.lock")
BREADCRUMB = os.path.join(HERE, ".oda_session.json")
STATUS_URL = "https://status.oda.sas.com/"
STATUS_API_URL = "https://status.oda.sas.com/api/v2/status.json"
ORPHAN_SWEEP_COOLDOWN = 90
MIN_RECOMMEND_SUCCESSES = 3

# Full workspace-server sets per ODA home region (brief §2.1). Region is DETECTED from the
# user's sascfg_personal.py, never hardcoded; this only expands a short iomhost to the full set
# so SASPy can fail over across every spawner in the region.
REGION_HOSTS = {
    "usw2":    ["odaws01-usw2", "odaws02-usw2", "odaws03-usw2", "odaws04-usw2"],
    "usw2-2":  ["odaws01-usw2-2", "odaws02-usw2-2"],
    "euw1":    ["odaws01-euw1", "odaws02-euw1"],
    "apse1":   ["odaws01-apse1", "odaws02-apse1"],
    "apse1-2": ["odaws01-apse1-2", "odaws02-apse1-2"],
}
_DOMAIN = ".oda.sas.com"

# Error taxonomy (brief §3.2). FAIL_FAST classes never consume the retry budget.
FAIL_FAST = {"AUTH", "CONFIG_ENCRYPTION"}
# Extra cooldown (seconds) applied BEFORE normal backoff for these classes.
COOLDOWN = {"SESSION_LIMIT": 90, "SPAWN_FAILED": 30}
KILL_SIGNAL = getattr(signal, "SIGKILL", signal.SIGTERM)


class OdaFatal(Exception):
    """Non-retryable failure (auth / encryption config). Caller must fix and re-run."""
    def __init__(self, error_class, detail=""):
        self.error_class = error_class
        super().__init__(f"{error_class}: {detail}".strip(": "))


class OdaExhausted(Exception):
    """Retry budget (max_wait_s) exhausted without a live workspace."""
    def __init__(self, last_class, attempts):
        self.last_class = last_class
        self.attempts = attempts
        super().__init__(f"ODA unavailable after {attempts} attempts (last: {last_class})")


class OdaExecTimeout(Exception):
    """A submitted SAS step exceeded its wall-clock deadline; the workspace is presumed hung.
    connect()'s budget only covers the CONNECT phase — once connected, a wedged server-side
    workspace would otherwise block submit() forever (the execution half of the zombie-session
    failure mode). The caller must teardown(sas, force=True) to reap the wedged session."""
    def __init__(self, timeout_s):
        self.timeout_s = timeout_s
        super().__init__(f"SAS submit exceeded {timeout_s}s wall-clock; workspace presumed hung")


class OdaConnection:
    """A live, probe-verified ODA session plus the metadata cibuild writes to health JSON."""
    def __init__(self, sas, endpoint, attempts, total_wait_s, probe_nonce_echoed,
                 failover_status=None):
        self.sas = sas
        self.endpoint = endpoint
        self.attempts = attempts
        self.total_wait_s = round(total_wait_s, 1)
        self.probe_nonce_echoed = probe_nonce_echoed
        self.failover_status = failover_status or {}
        self._closed = False

    def close(self, *, force=False):
        """Release this session. Idempotent wrapper around teardown()."""
        if not self._closed:
            teardown(self.sas, force=force)
            self._closed = True

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()
        return False


# --------------------------------------------------------------------------- region / config
def _read_oda_cfg(cfg_file=CFG_FILE):
    """Return the oda/ODA config dict from sascfg_personal.py, or {}. Never prints secrets."""
    ns = {}
    try:
        with open(cfg_file, "r", encoding="utf-8") as f:
            exec(compile(f.read(), cfg_file, "exec"), ns)  # user's own trusted config
    except (OSError, SyntaxError):
        return {}
    for key in ("oda", "ODA"):
        cfg = ns.get(key)
        if isinstance(cfg, dict):
            return cfg
    return {}


def _read_iomhost(cfg_file=CFG_FILE):
    """Return the iomhost value from sascfg_personal.py (str or list), or None. Read-only;
    never prints secrets."""
    return _read_oda_cfg(cfg_file).get("iomhost")


def _configured_hosts(cfg_file=CFG_FILE):
    """Return configured iomhost values as fully-qualified hosts. Secrets are never read/returned."""
    iomhost = _read_iomhost(cfg_file)
    hosts = iomhost if isinstance(iomhost, list) else ([iomhost] if iomhost else [])
    out = []
    for h in hosts:
        h = str(h).strip()
        if h:
            out.append(h if h.endswith(_DOMAIN) else f"{h}{_DOMAIN}")
    return out


def detect_region_hosts(cfg_file=CFG_FILE):
    """Detect the ODA region from the configured iomhost and return (region, [fqdn,...]) — the
    FULL spawner set for that region so SASPy can fail over. Falls back to (None, configured)."""
    import re
    iomhost = _read_iomhost(cfg_file)
    hosts = iomhost if isinstance(iomhost, list) else ([iomhost] if iomhost else [])
    region = None
    for h in hosts:
        m = re.match(r"^odaws\d+-(.+?)(?:\.oda\.sas\.com)?$", str(h).strip())
        if m and m.group(1) in REGION_HOSTS:
            region = m.group(1)
            break
    if region:
        return region, [f"{h}{_DOMAIN}" for h in REGION_HOSTS[region]]
    # Unknown region: keep whatever was configured (fully-qualified).
    return None, _configured_hosts(cfg_file)


def failover_status(cfg_file=CFG_FILE):
    """Summarize whether sascfg_personal.py has the full regional ODA host list configured.

    saspy's ODA config ignores runtime iomhost overrides, so real spawner failover only happens
    when the user's cfg file contains every host for the detected region. This returns a
    telemetry-safe status only: hostnames and booleans, never credentials.
    """
    configured = _configured_hosts(cfg_file)
    region, recommended = detect_region_hosts(cfg_file)
    missing = [h for h in recommended if h not in configured]
    return {
        "oda_region": region,
        "oda_configured_hosts": configured,
        "oda_recommended_hosts": recommended,
        "oda_missing_failover_hosts": missing,
        "oda_failover_configured": bool(region and recommended and not missing),
    }


def preflight(cfg_file=CFG_FILE, authinfo_path=None, java_cmd=None, port_check=False,
              which_fn=shutil.which, exists_fn=os.path.exists, stat_fn=os.stat,
              run_fn=subprocess.run, saspy_importer=None):
    """Credential-safe local readiness check for SASPy/ODA.

    Required checks cover local prerequisites that make a real ODA launch impossible before the
    broker even reaches ODA: Java, saspy import, config file, authinfo file/mode, and iomhost.
    Optional port checks are advisory because VPN/firewall state can change between preflight and
    connect; the broker's retry state machine remains the authority for transient availability.
    """
    cfg = _read_oda_cfg(cfg_file)
    authinfo_path = authinfo_path or os.path.join(os.path.expanduser("~"), ".authinfo")
    java_candidate = java_cmd or cfg.get("java") or which_fn("java")
    required = {}
    advisory = {}

    java_path = which_fn(java_candidate) if java_candidate else None
    if not java_path and java_candidate and exists_fn(str(java_candidate)):
        java_path = str(java_candidate)
    required["java"] = bool(java_path)
    if java_path:
        try:
            p = run_fn([java_path, "-version"], capture_output=True, text=True, timeout=10)
            version_line = (p.stderr or p.stdout).splitlines()[0] if (p.stderr or p.stdout) else ""
            advisory["java_path"] = java_path
            advisory["java_version"] = version_line
        except Exception as e:
            required["java"] = False
            advisory["java_error"] = f"{type(e).__name__}: {str(e)[:120]}"

    try:
        if saspy_importer is None:
            import saspy
        else:
            saspy = saspy_importer()
        required["saspy"] = True
        advisory["saspy_version"] = getattr(saspy, "__version__", "unknown")
    except Exception as e:
        required["saspy"] = False
        advisory["saspy_error"] = f"{type(e).__name__}: {str(e)[:120]}"

    required["cfg_file"] = bool(cfg)
    required["iomhost"] = bool(cfg.get("iomhost"))
    required["authkey"] = bool(cfg.get("authkey"))

    try:
        st = stat_fn(authinfo_path)
        mode = st.st_mode & 0o777
        required["authinfo"] = True
        required["authinfo_mode_600"] = mode == 0o600
        advisory["authinfo_path"] = authinfo_path
        advisory["authinfo_mode"] = oct(mode)
    except OSError:
        required["authinfo"] = False
        required["authinfo_mode_600"] = False
        advisory["authinfo_path"] = authinfo_path

    failover = failover_status(cfg_file)
    if port_check:
        import socket
        reach = {}
        for host in failover["oda_configured_hosts"]:
            try:
                with socket.create_connection((host, int(cfg.get("iomport", 8591))), timeout=3):
                    reach[host] = True
            except OSError:
                reach[host] = False
        advisory["oda_port_8591_reachable"] = reach

    missing = [k for k, v in required.items() if not v]
    out = {
        "oda_preflight_ok": not missing,
        "oda_preflight_missing": missing,
        "oda_preflight_required": required,
        "oda_preflight_advisory": advisory,
    }
    out.update(failover)
    return out


# --------------------------------------------------------------------------- classification
def classify(exc_text):
    """Map an exception/log string to an error class (brief §3.2)."""
    t = (exc_text or "").lower()
    if any(k in t for k in ("invalid login", "authentication", "credential", "user/password",
                            "could not be authenticated")):
        return "AUTH"
    if any(k in t for k in ("encryption key exchange", "aes", "encryption")):
        return "CONFIG_ENCRYPTION"
    if "session" in t and ("limit" in t or "maximum" in t or "too many" in t):
        return "SESSION_LIMIT"
    if "could not connect to any server in the cluster" in t:
        return "CLUSTER_UNAVAILABLE"
    if any(k in t for k in ("spawner", "terminated unexpectedly", "rc from wait was",
                            "no sas process")):
        return "SPAWN_FAILED"
    if any(k in t for k in ("getaddrinfo", "timed out", "timeout", "10060", "connection refused",
                            "network is unreachable")):
        return "NETWORK"
    return "SPAWN_FAILED"  # default: treat unknown connect failures as a (bounded) spawn issue


# --------------------------------------------------------------------------- ledger
def log_attempt(record, ledger=LEDGER):
    """Append one attempt record (jsonl) to the ledger. Best-effort; never raises."""
    rec = dict(record)
    rec.setdefault("ts", datetime.datetime.now().astimezone().isoformat())
    try:
        with open(ledger, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec) + "\n")
    except OSError:
        pass


def _read_ledger(ledger=LEDGER):
    out = []
    try:
        with open(ledger, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        out.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
    except OSError:
        pass
    return out


def recommend_window(ledger=LEDGER, min_successes=MIN_RECOMMEND_SUCCESSES):
    """Bucket successful connects by local hour-of-day and return the best contiguous window as
    'HH:00-HH:00' (local), or None until there are enough successes to infer a pattern."""
    recs = _read_ledger(ledger)
    succ = [r for r in recs if not r.get("error_class")]
    if len(succ) < min_successes:
        return None
    hist = [0] * 24
    for r in succ:
        ts = r.get("ts", "")
        try:
            h = datetime.datetime.fromisoformat(ts).hour
            hist[h] += 1
        except (ValueError, TypeError):
            continue
    if not any(hist):
        return None
    # best 3-hour contiguous window
    best_start, best_sum = 0, -1
    for s in range(24):
        tot = sum(hist[(s + k) % 24] for k in range(3))
        if tot > best_sum:
            best_sum, best_start = tot, s
    return f"{best_start:02d}:00-{(best_start + 3) % 24:02d}:00 (local)"


# --------------------------------------------------------------------------- slot hygiene
class _SingleFlight:
    """fcntl-based POSIX lock so two processes never spawn an ODA workspace at once."""
    def __init__(self, path=LOCKFILE, enabled=True):
        self.path, self.enabled, self._fh = path, enabled, None

    def __enter__(self):
        if not self.enabled:
            return self
        if os.name != "posix":
            raise OdaFatal("CONFIG_UNSUPPORTED", "ODA broker locking requires a POSIX client")
        import fcntl
        self._fh = open(self.path, "w")
        fcntl.flock(self._fh, fcntl.LOCK_EX)
        return self

    def __exit__(self, *exc):
        if self._fh is not None:
            try:
                import fcntl
                fcntl.flock(self._fh, fcntl.LOCK_UN)
                self._fh.close()
            except (OSError, ValueError):
                pass
        return False


def _write_breadcrumb(endpoint):
    try:
        with open(BREADCRUMB, "w", encoding="utf-8") as f:
            json.dump({"pid": os.getpid(), "endpoint": endpoint,
                       "ts": datetime.datetime.now().astimezone().isoformat()}, f)
    except OSError:
        pass


def _clear_breadcrumb():
    try:
        os.remove(BREADCRUMB)
    except OSError:
        pass


def sweep_orphans():
    """If a prior process left a session breadcrumb (crashed without teardown), we cannot
    re-attach to it from here, but its presence signals ODA may still be holding that slot.
    Clear the breadcrumb and report so the caller applies a cooldown before spawning. A true
    cross-process reap isn't possible client-side; the single-flight lock + explicit teardown
    (or OdaConnection's context-manager close) are what prevent orphans going forward."""
    if os.path.exists(BREADCRUMB):
        try:
            with open(BREADCRUMB, "r", encoding="utf-8") as f:
                info = json.load(f)
        except (OSError, json.JSONDecodeError):
            info = {}
        _clear_breadcrumb()
        return info or {"stale": True}
    return None


def _call_with_timeout(fn, timeout_s):
    """Run fn() in a DAEMON thread and return once it completes OR timeout_s elapses (whichever
    first). Returns True if fn finished within the budget, else False. Never propagates fn's
    exception. The daemon thread means a still-hung fn can never block interpreter exit."""
    import threading
    done = threading.Event()
    def _run():
        try:
            fn()
        except Exception:
            pass
        finally:
            done.set()
    threading.Thread(target=_run, daemon=True, name="oda-endsas").start()
    return done.wait(timeout_s)


def _session_child_pid(sas):
    """Best-effort OS pid of the LOCAL subprocess saspy spawned for this session — the Java IOM
    gateway for ODA (a Popen, so `.pid` is its int) or a bare int pid for stdio/ssh. Returns None
    if not discoverable or already reaped (saspy nulls `_io.pid` after a clean endsas). Never
    raises; reads saspy internals defensively."""
    try:
        p = getattr(getattr(sas, "_io", None), "pid", None)
        p = getattr(p, "pid", p)   # Popen -> its .pid; bare int -> itself
        if isinstance(p, int) and p > 0:
            return p
    except Exception:
        pass
    return None


def _pid_alive(pid):
    """True if `pid` is a live process (signal 0 probe). Never raises."""
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def teardown(sas, *, force=False, endsas_timeout=20.0,
             kill_fn=os.kill, alive_fn=_pid_alive, call_with_timeout=_call_with_timeout):
    """End a session, clear its breadcrumb, and force-kill the lingering local SAS/Java child.
    Never raises.

    A graceful endsas() can ITSELF hang when the IOM workspace is wedged (the symptom behind the
    zombie sessions: a local Java gateway stuck at 100% CPU). So we (a) run endsas() under a
    wall-clock cap and (b) force-kill the local child subprocess if it is still alive afterwards.

    force=True is used after an execution-phase timeout, when a worker thread may STILL be blocked
    inside submit() on this same session: calling endsas() then would race that thread on the
    shared IOM socket, so we skip the graceful close and go straight to the child kill (which also
    unblocks that worker by tearing the socket out from under it).

    NOTE: this reaps the LOCAL gateway only. The server-side ODA workspace slot is released by
    ODA's own reaper on its schedule, not client-side — there is no client API to free it."""
    pid = _session_child_pid(sas)   # capture BEFORE endsas (a clean endsas nulls it)
    if sas is not None and not force:
        call_with_timeout(lambda: sas.endsas(), endsas_timeout)
    if pid is not None and alive_fn(pid):
        try:
            kill_fn(pid, KILL_SIGNAL)
        except OSError:
            pass
    _clear_breadcrumb()


def submit_timed(sas, code, *, timeout_s=1800):
    """sas.submit(code) under a wall-clock deadline. Returns the saspy result dict on success;
    raises OdaExecTimeout if the workspace stalls past timeout_s. The submit runs in a daemon
    worker thread; on timeout we deliberately do NOT touch `sas` here — the caller's
    `teardown(sas, force=True)` will SIGKILL the gateway, which unblocks this thread. Any
    exception raised inside submit() is re-raised in the caller's thread unchanged."""
    import threading
    box = {}
    def _run():
        try:
            box["r"] = sas.submit(code)
        except Exception as e:  # noqa: BLE001 — re-raised below in the caller thread
            box["e"] = e
    t = threading.Thread(target=_run, daemon=True, name="oda-submit")
    t.start()
    t.join(timeout_s)
    if t.is_alive():
        raise OdaExecTimeout(timeout_s)
    if "e" in box:
        raise box["e"]
    return box.get("r", {})


# --------------------------------------------------------------------------- defaults (real)
def _status_from_statuspage_json(body):
    """Map Statuspage API JSON to broker status. Unknown shapes stay advisory."""
    try:
        payload = json.loads(body)
    except (TypeError, json.JSONDecodeError):
        return "unknown"
    indicator = str(payload.get("status", {}).get("indicator", "")).lower()
    if indicator == "none":
        return "healthy"
    if indicator in {"minor", "major", "critical"}:
        return "unhealthy"
    return "unknown"


def _status_from_html(body):
    """Conservative HTML fallback: only strong healthy phrases are trusted."""
    t = (body or "").lower()
    if "all systems operational" in t or "no incidents reported" in t:
        return "healthy"
    return "unknown"


def _default_status_poller(_cache={"t": 0.0, "v": "unknown"}):
    """Return 'healthy' / 'unhealthy' / 'unknown' from status.oda.sas.com (cached ~60s).
    Unreachable or unparsable status page -> 'unknown' (advisory only; we still attempt)."""
    now = time.time()
    if now - _cache["t"] < 60:
        return _cache["v"]
    state = "unknown"
    try:
        import urllib.request
        with urllib.request.urlopen(STATUS_API_URL, timeout=8) as resp:
            body = resp.read(20000).decode("utf-8", "replace").lower()
        state = _status_from_statuspage_json(body)
    except Exception:
        try:
            import urllib.request
            with urllib.request.urlopen(STATUS_URL, timeout=8) as resp:
                body = resp.read(20000).decode("utf-8", "replace")
            state = _status_from_html(body)
        except Exception:
            state = "unknown"
    _cache["t"], _cache["v"] = now, state
    return state


def _default_session_factory(timeout):
    """Build a saspy SASsession for ODA. Imported lazily so this module loads without
    saspy/Java present (e.g. on CI / for unit tests).

    NOTE: saspy IGNORES `iomhost`/`iomport` passed as SASsession kwargs for an ODA config
    ("Parameter ... ignored due to configuration restriction"). **Multi-server spawner
    failover must therefore be set as an iomhost LIST in `sascfg_personal.py`**, e.g.
    `'iomhost': ['odaws01-apse1.oda.sas.com', 'odaws02-apse1.oda.sas.com']`, so saspy itself
    fails over across the region's workspace servers. We rely on the cfg file and only derive
    a region label here for telemetry; `detect_region_hosts()` reports the configured set."""
    import saspy
    region, hosts = detect_region_hosts()
    sas = saspy.SASsession(cfgname="oda", cfgfile=CFG_FILE, timeout=timeout)
    return sas, (hosts[0] if hosts else "oda")


def _default_prober(sas, nonce):
    """Live round-trip: submit a runtime nonce and confirm BOTH it echoes back AND the workspace
    macro vars resolve. A cached/dead session cannot echo a fresh nonce, so 'oda' is earned."""
    import re
    try:
        log = sas.submit(f"%put ODA_LIVE=&sysjobid.|{nonce}|&sysscp.;").get("LOG", "")
    except Exception:
        return False
    # Match the RESOLVED %put output (e.g. 'ODA_LIVE=96545|<nonce>|LIN X64'), NOT an
    # "&sysjobid absent" check: SAS echoes the SOURCE line too when SOURCE is on (the ODA
    # default for an saspy submit), and that echo always contains the literal '&sysjobid.',
    # which defeats an absence test and falsely fails every live session. A '&'-free segment
    # flanking the fresh nonce can only come from resolved output, never from echoed source.
    return bool(re.search(rf"ODA_LIVE=[^&|\n]*\|{re.escape(nonce)}\|[^&\n]*", log))


def _jittered(base, cap, n):
    """Full-jitter exponential backoff: random in [0, min(cap, base*2**n)]."""
    return random.uniform(0, min(cap, base * (2 ** n)))


def _sleep_within_deadline(delay_s, deadline, clock, sleep_fn):
    """Sleep no longer than the remaining connect budget. Returns False if no budget remains."""
    remaining = deadline - clock()
    if remaining <= 0:
        return False
    sleep_fn(min(max(0, delay_s), remaining))
    return True


# --------------------------------------------------------------------------- the broker
def connect(max_wait_s=3600, base=5, cap=120, *,
            timeout=90,
            session_factory=None, status_poller=None, prober=None,
            sleep_fn=time.sleep, clock=time.monotonic, lock=True,
            jitter=_jittered):
    """Open a probe-verified ODA session, riding transient spawner/cluster timeouts within a
    wall-clock budget. Raises OdaFatal (fix-and-rerun classes) or OdaExhausted (budget spent).

    All side-effecting collaborators are injectable for testing."""
    session_factory = session_factory or _default_session_factory
    status_poller = status_poller or _default_status_poller
    prober = prober or _default_prober

    start = clock()
    deadline = start + max_wait_s
    attempt = 0
    last_class = None
    failover = failover_status()

    with _SingleFlight(enabled=lock):
        stale = sweep_orphans()
    if stale:
        # A prior run may still hold a slot server-side; let ODA's reaper catch up.
        last_class = "ORPHAN_SWEEP"
        log_attempt({"error_class": "ORPHAN_SWEEP", "detail": str(stale)})
        if not _sleep_within_deadline(min(cap, ORPHAN_SWEEP_COOLDOWN),
                                      deadline, clock, sleep_fn):
            raise OdaExhausted("ORPHAN_SWEEP", attempt)

    while clock() < deadline:
        state = status_poller()
        if state == "unhealthy":
            last_class = "SERVICE_DOWN"
            log_attempt({"error_class": "SERVICE_DOWN", "status_state": state})
            _sleep_within_deadline(jitter(base, cap, attempt), deadline, clock, sleep_fn)
            attempt += 1
            continue

        with _SingleFlight(enabled=lock):
            if clock() >= deadline:
                break
            t0 = clock()
            sas = None
            try:
                sas, endpoint = session_factory(timeout)
                _write_breadcrumb(endpoint)
                nonce = f"{os.getpid()}-{random.randint(10**6, 10**7)}"
                if prober(sas, nonce):
                    log_attempt({"error_class": None, "host": endpoint,
                                 "latency_s": round(clock() - t0, 1),
                                 "status_state": state, "attempt": attempt + 1})
                    return OdaConnection(sas, endpoint, attempt + 1, clock() - start, True,
                                         failover)
                # Connected but workspace never came alive — treat as spawn failure.
                # Teardown stays under the spawn lock so another process cannot consume a slot
                # while this failed workspace is still being closed or force-reaped.
                teardown(sas); sas = None
                last_class = "SPAWN_FAILED"
                log_attempt({"error_class": "SPAWN_FAILED", "detail": "probe failed",
                             "latency_s": round(clock() - t0, 1), "status_state": state})
            except Exception as e:
                last_class = classify(str(e))
                # Keep cleanup serialized with spawn attempts for slot hygiene; teardown itself
                # is capped by endsas_timeout and force-kills the local gateway if needed.
                teardown(sas); sas = None
                log_attempt({"error_class": last_class, "detail": str(e).splitlines()[0][:160]
                             if str(e) else "", "latency_s": round(clock() - t0, 1),
                             "status_state": state})
                if last_class in FAIL_FAST:
                    raise OdaFatal(last_class, str(e).splitlines()[0] if str(e) else "")

        cooldown = COOLDOWN.get(last_class, 0)
        _sleep_within_deadline(cooldown + jitter(base, cap, attempt),
                               deadline, clock, sleep_fn)
        attempt += 1

    raise OdaExhausted(last_class, attempt)
