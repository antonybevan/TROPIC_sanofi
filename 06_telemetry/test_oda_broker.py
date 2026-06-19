"""
Unit tests for the ODA resilience layer (broker + seed). No Java, network, or live ODA needed —
every collaborator is injected. Run:  python3 06_telemetry/test_oda_broker.py
Covers acceptance criteria §7: earned-mode (probe), teardown on failed spawn, fail-fast classes,
backoff-not-blind-loop, idempotent seed, unverified-library detection.
"""
import os
import sys
import json
import glob
import signal
import threading
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import oda_broker as B
import seed_sdtm as S


class FakeClock:
    """Time advances ONLY via sleep — deterministic budget control."""
    def __init__(self): self.t = 0.0
    def read(self): return self.t
    def sleep(self, d): self.t += d


class FakeSas:
    def __init__(self, remote_manifest=None, nobs_log=""):
        self.uploaded, self.ended = [], False
        self.remote_manifest, self.nobs_log = remote_manifest, nobs_log
    def upload(self, local, remote, **kw): self.uploaded.append(os.path.basename(remote))
    def download(self, local, remote, **kw):
        if self.remote_manifest is None:
            raise RuntimeError("file not found on ODA")
        with open(local, "w") as f:
            json.dump(self.remote_manifest, f)
    def submit(self, code):
        # _ensure_remote_dir issues an mkdir-tree step and checks for a success marker; report
        # the tree as present. Every other submit (nobs integrity re-read) returns nobs_log.
        if "TROPIC_MKDIR" in code:
            return {"LOG": "TROPIC_MKDIR|/x|1\n"}
        return {"LOG": self.nobs_log}
    def endsas(self): self.ended = True


CONST_JITTER = lambda base, cap, n: 1.0
HEALTHY = lambda: "healthy"


class TestClassify(unittest.TestCase):
    def test_taxonomy(self):
        self.assertEqual(B.classify("invalid login: user/password"), "AUTH")
        self.assertEqual(B.classify("encryption key exchange failed"), "CONFIG_ENCRYPTION")
        self.assertEqual(B.classify("session limit reached: maximum"), "SESSION_LIMIT")
        self.assertEqual(B.classify("could not connect to any server in the cluster"), "CLUSTER_UNAVAILABLE")
        self.assertEqual(B.classify("SAS process has terminated unexpectedly"), "SPAWN_FAILED")
        self.assertEqual(B.classify("getaddrinfo failed"), "NETWORK")


class TestBroker(unittest.TestCase):
    def setUp(self):
        # Isolate broker side-effects (breadcrumb/ledger) to a temp dir per test so a
        # live session's breadcrumb can't leak an orphan-sweep cooldown into the next test.
        self._td = tempfile.mkdtemp()
        self._orig = (B.BREADCRUMB, B.LEDGER, B.LOCKFILE)
        B.BREADCRUMB = os.path.join(self._td, "crumb.json")
        B.LEDGER = os.path.join(self._td, "ledger.json")
        B.LOCKFILE = os.path.join(self._td, "lock")

    def tearDown(self):
        B.BREADCRUMB, B.LEDGER, B.LOCKFILE = self._orig

    def test_probe_failure_never_yields_oda(self):
        """A connected-but-dead workspace (probe fails) must NOT return a session; mode falls to
        sim (caller catches OdaExhausted). Teardown must run on the dead session."""
        sas = FakeSas()
        clk = FakeClock()
        with self.assertRaises(B.OdaExhausted):
            B.connect(max_wait_s=3, lock=False, jitter=CONST_JITTER,
                      clock=clk.read, sleep_fn=clk.sleep, status_poller=HEALTHY,
                      session_factory=lambda t: (sas, "odaws01-apse1.oda.sas.com"),
                      prober=lambda s, n: False)
        self.assertTrue(sas.ended, "teardown() must be called on the failed-spawn session")

    def test_live_probe_earns_oda(self):
        sas = FakeSas()
        clk = FakeClock()
        conn = B.connect(max_wait_s=10, lock=False, jitter=CONST_JITTER,
                         clock=clk.read, sleep_fn=clk.sleep, status_poller=HEALTHY,
                         session_factory=lambda t: (sas, "odaws03-usw2.oda.sas.com"),
                         prober=lambda s, n: True)
        self.assertIs(conn.sas, sas)
        self.assertEqual(conn.endpoint, "odaws03-usw2.oda.sas.com")
        self.assertTrue(conn.probe_nonce_echoed)
        self.assertGreaterEqual(conn.attempts, 1)
        B.teardown(conn.sas)  # caller owns the live session; tear it down

    def test_auth_fails_fast_without_consuming_budget(self):
        calls = {"n": 0}
        def factory(t):
            calls["n"] += 1
            raise RuntimeError("ERROR: Invalid login: user/password could not be authenticated")
        clk = FakeClock()
        with self.assertRaises(B.OdaFatal) as ctx:
            B.connect(max_wait_s=3600, lock=False, jitter=CONST_JITTER,
                      clock=clk.read, sleep_fn=clk.sleep, status_poller=HEALTHY,
                      session_factory=factory, prober=lambda s, n: True)
        self.assertEqual(ctx.exception.error_class, "AUTH")
        self.assertEqual(calls["n"], 1, "AUTH must abort on first attempt, not loop")

    def test_backoff_is_jittered_not_blind(self):
        """Transient failures retry via injected jitter (no fixed sleep); budget is the bound."""
        sleeps = []
        clk = FakeClock()
        def rec_sleep(d): sleeps.append(d); clk.sleep(d)
        with self.assertRaises(B.OdaExhausted):
            B.connect(max_wait_s=3, lock=False, jitter=CONST_JITTER,
                      clock=clk.read, sleep_fn=rec_sleep, status_poller=HEALTHY,
                      session_factory=lambda t: (_ for _ in ()).throw(
                          RuntimeError("SAS process has terminated unexpectedly")),
                      prober=lambda s, n: True)
        self.assertTrue(sleeps, "must back off between attempts")
        # SPAWN_FAILED carries a cooldown; every sleep is bounded and non-negative.
        self.assertTrue(all(s >= 0 for s in sleeps))

    def test_recommend_window(self):
        led = os.path.join(tempfile.mkdtemp(), "ledger.json")
        self.assertIsNone(B.recommend_window(led))
        with open(led, "w") as f:
            for h in (14, 14, 15):
                f.write(json.dumps({"ts": f"2026-06-12T{h:02d}:30:00+05:30",
                                    "error_class": None}) + "\n")
        win = B.recommend_window(led)
        self.assertIsNotNone(win)
        self.assertRegex(win, r"\d{2}:00-\d{2}:00")


class TestProber(unittest.TestCase):
    """Regression: the live probe must read the RESOLVED %put output, not assert that
    '&sysjobid' is absent. ODA echoes the SOURCE line (which contains the literal
    '&sysjobid.') by default, which previously failed every live session as SPAWN_FAILED."""
    NONCE = "12345-9999999"

    def _sas(self, log):
        return type("S", (), {"submit": lambda self, code, _log=log: {"LOG": _log}})()

    def test_resolved_output_with_echoed_source_passes(self):
        # Real ODA log: line 26 echoes the source (literal &sysjobid.), then the resolved output.
        n = self.NONCE
        log = (f"26   %put ODA_LIVE=&sysjobid.|{n}|&sysscp.;\n"
               f"ODA_LIVE=97614|{n}|LIN X64\n")
        self.assertTrue(B._default_prober(self._sas(log), n))

    def test_stale_log_without_nonce_fails(self):
        log = "ODA_LIVE=97614|some-OTHER-nonce|LIN X64\n"
        self.assertFalse(B._default_prober(self._sas(log), self.NONCE))

    def test_unresolved_macro_fails(self):
        # Workspace not really live: macro never resolved, only the echoed source carries the nonce.
        n = self.NONCE
        log = (f"26   %put ODA_LIVE=&sysjobid.|{n}|&sysscp.;\n"
               "WARNING: Apparent symbolic reference SYSJOBID not resolved.\n")
        self.assertFalse(B._default_prober(self._sas(log), n))

    def test_submit_exception_fails(self):
        sas = type("S", (), {"submit": lambda self, code: (_ for _ in ()).throw(RuntimeError("dead"))})()
        self.assertFalse(B._default_prober(sas, self.NONCE))


class TestSeedIdempotent(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        for name, data in (("dm.sas7bdat", b"AAAA"), ("ae.sas7bdat", b"BBBBBB")):
            with open(os.path.join(self.d, name), "wb") as f:
                f.write(data)
        self.local = S.compute_local_manifest(self.d)

    def test_manifest_match_skips_upload(self):
        sas = FakeSas(remote_manifest=self.local)  # ODA already has exactly this source
        res = S.seed(sas, sdtm_dir=self.d, remote_dir="/x", force=False)
        self.assertEqual(res["status"], "already-resident")
        self.assertEqual(res["uploaded"], 0)
        self.assertEqual(sas.uploaded, [], "must perform ZERO uploads when manifest matches")

    def test_missing_remote_manifest_triggers_seed(self):
        sas = FakeSas(remote_manifest=None)  # nothing on ODA -> not resident
        ok, _, reason = S.verify_resident(sas, sdtm_dir=self.d, remote_dir="/x", local=self.local)
        self.assertFalse(ok)
        res = S.seed(sas, sdtm_dir=self.d, remote_dir="/x", force=False)
        self.assertEqual(res["status"], "seeded")
        # uploaded the 2 data files + the manifest sentinel (written LAST)
        self.assertIn(S.MANIFEST_NAME, sas.uploaded)
        self.assertEqual(sas.uploaded[-1], S.MANIFEST_NAME, "manifest must be uploaded LAST")

    def test_changed_source_fails_match(self):
        stale = json.loads(json.dumps(self.local))
        stale["datasets"]["dm.sas7bdat"]["sha256"] = "deadbeef"
        self.assertFalse(S.manifests_match(self.local, stale))

    def test_force_overrides_resident(self):
        sas = FakeSas(remote_manifest=self.local)
        res = S.seed(sas, sdtm_dir=self.d, remote_dir="/x", force=True)
        self.assertEqual(res["status"], "seeded")
        self.assertGreater(len(sas.uploaded), 0)

    def test_stale_members_selects_only_changed(self):
        # Pure diff: a single changed member; absent/forced manifest -> the whole library.
        remote = json.loads(json.dumps(self.local))
        remote["datasets"]["dm.sas7bdat"]["sha256"] = "changed"
        self.assertEqual(S.stale_members(self.local, remote), ["dm.sas7bdat"])
        self.assertEqual(S.stale_members(self.local, None), ["ae.sas7bdat", "dm.sas7bdat"])
        self.assertEqual(S.stale_members(self.local, self.local, force=True),
                         ["ae.sas7bdat", "dm.sas7bdat"])

    def test_partial_change_uploads_only_delta(self):
        # ODA has a matching dm but a STALE ae -> only ae (+ the manifest) must upload; the
        # ~200 MB cost should track the delta, not the whole library.
        remote = json.loads(json.dumps(self.local))
        remote["datasets"]["ae.sas7bdat"]["sha256"] = "stale-ae-hash"
        sas = FakeSas(remote_manifest=remote)
        res = S.seed(sas, sdtm_dir=self.d, remote_dir="/x", force=False)
        self.assertEqual(res["status"], "seeded")
        self.assertEqual((res["uploaded"], res["skipped"]), (1, 1))
        self.assertIn("ae.sas7bdat", sas.uploaded)
        self.assertNotIn("dm.sas7bdat", sas.uploaded)       # unchanged member NOT re-uploaded
        self.assertEqual(sas.uploaded[-1], S.MANIFEST_NAME)  # manifest still written LAST


class _FakeKillSas:
    """Session whose local child pid and endsas() are controllable for teardown tests."""
    def __init__(self, child_pid=None):
        self.ended = False
        if child_pid is not None:
            # mimic saspy IOM: sas._io.pid is a Popen whose .pid is the OS pid
            self._io = type("IO", (), {"pid": type("P", (), {"pid": child_pid})()})()
    def endsas(self):
        self.ended = True


def _kill_recorder():
    calls = []
    return calls, (lambda pid, sig: calls.append((pid, sig)))


# call_with_timeout stub that RUNS fn and reports completion (the normal, non-hung path)
_RAN = lambda fn, t: (fn(), True)[1]


class TestTeardownForceKill(unittest.TestCase):
    """Finding 2: teardown must force-kill the lingering local Java/SAS child so a wedged
    endsas() can't leave a CPU-burning zombie. The server-side ODA slot is ODA's to reap."""
    def setUp(self):
        self._td = tempfile.mkdtemp()
        self._orig = B.BREADCRUMB
        B.BREADCRUMB = os.path.join(self._td, "crumb.json")

    def tearDown(self):
        B.BREADCRUMB = self._orig

    def test_kills_alive_child_after_graceful_endsas(self):
        sas = _FakeKillSas(child_pid=4242)
        calls, kill = _kill_recorder()
        B.teardown(sas, kill_fn=kill, alive_fn=lambda pid: True, call_with_timeout=_RAN)
        self.assertTrue(sas.ended, "graceful endsas() must still be attempted")
        self.assertEqual(calls, [(4242, signal.SIGKILL)])

    def test_no_kill_when_child_already_dead(self):
        sas = _FakeKillSas(child_pid=4242)
        calls, kill = _kill_recorder()
        B.teardown(sas, kill_fn=kill, alive_fn=lambda pid: False, call_with_timeout=_RAN)
        self.assertTrue(sas.ended)
        self.assertEqual(calls, [], "a cleanly-ended session must not be SIGKILLed")

    def test_force_skips_endsas_but_kills(self):
        """force=True (post exec-timeout): a worker thread may still be blocked in submit() on
        this session, so endsas() must be SKIPPED (it would race that thread) and we kill."""
        sas = _FakeKillSas(child_pid=99)
        calls, kill = _kill_recorder()
        boom = lambda fn, t: (_ for _ in ()).throw(AssertionError("endsas must not run on force"))
        B.teardown(sas, force=True, kill_fn=kill, alive_fn=lambda pid: True, call_with_timeout=boom)
        self.assertFalse(sas.ended)
        self.assertEqual(calls, [(99, signal.SIGKILL)])

    def test_no_child_pid_no_kill(self):
        sas = _FakeKillSas(child_pid=None)  # no _io -> pid undiscoverable
        calls, kill = _kill_recorder()
        B.teardown(sas, kill_fn=kill, alive_fn=lambda pid: True, call_with_timeout=_RAN)
        self.assertTrue(sas.ended)
        self.assertEqual(calls, [])

    def test_none_session_is_safe(self):
        calls, kill = _kill_recorder()
        B.teardown(None, kill_fn=kill, alive_fn=lambda pid: True, call_with_timeout=_RAN)
        self.assertEqual(calls, [])  # nothing to end or kill; must not raise


class TestSessionChildPid(unittest.TestCase):
    def test_popen_like(self):
        self.assertEqual(B._session_child_pid(_FakeKillSas(child_pid=777)), 777)

    def test_bare_int_pid(self):
        sas = type("S", (), {"_io": type("IO", (), {"pid": 555})()})()
        self.assertEqual(B._session_child_pid(sas), 555)

    def test_none_when_no_io_or_reaped(self):
        self.assertIsNone(B._session_child_pid(object()))
        self.assertIsNone(B._session_child_pid(None))
        reaped = type("S", (), {"_io": type("IO", (), {"pid": None})()})()
        self.assertIsNone(B._session_child_pid(reaped))


class TestCallWithTimeout(unittest.TestCase):
    def test_quick_fn_completes(self):
        ran = []
        self.assertTrue(B._call_with_timeout(lambda: ran.append(1), 2.0))
        self.assertEqual(ran, [1])

    def test_hung_fn_times_out(self):
        block = threading.Event()
        try:
            self.assertFalse(B._call_with_timeout(lambda: block.wait(30), 0.15))
        finally:
            block.set()  # release the daemon worker


class TestSubmitTimed(unittest.TestCase):
    """Finding 3: a wedged server-side workspace must not block submit() forever."""
    def test_returns_result_on_quick_submit(self):
        sas = type("S", (), {"submit": lambda self, code: {"LOG": "ok"}})()
        self.assertEqual(B.submit_timed(sas, "x", timeout_s=2)["LOG"], "ok")

    def test_raises_exec_timeout_on_hang(self):
        block = threading.Event()
        sas = type("S", (), {"submit": lambda self, code: block.wait(30)})()
        try:
            with self.assertRaises(B.OdaExecTimeout):
                B.submit_timed(sas, "x", timeout_s=0.15)
        finally:
            block.set()

    def test_propagates_submit_exception_unchanged(self):
        sas = type("S", (), {"submit": lambda self, code:
                             (_ for _ in ()).throw(RuntimeError("boom"))})()
        with self.assertRaises(RuntimeError):
            B.submit_timed(sas, "x", timeout_s=2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
