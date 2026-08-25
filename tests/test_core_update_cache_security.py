"""Security tests for the CDISC Library credential-to-cache boundary."""

from __future__ import annotations

import importlib.util
import io
import os
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "platform/run_core_update_cache.py"
SPEC = importlib.util.spec_from_file_location("run_core_update_cache", MODULE_PATH)
assert SPEC and SPEC.loader
run_core_update_cache = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(run_core_update_cache)


def _credential_file(tmp_path: Path, content: str, mode: int = 0o600) -> Path:
    path = tmp_path / ".env"
    path.write_text(content, encoding="utf-8")
    path.chmod(mode)
    return path


def _arguments(path: Path) -> list[str]:
    return [str(path), "/controlled/python", "/controlled/core.py", "/controlled/cache"]


def test_wrapper_nofollow_loads_exact_0600_file_and_scopes_key_to_child(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.delenv("CDISC_LIBRARY_API_KEY", raising=False)
    monkeypatch.setenv("TROPIC_INHERITED_CDISC_LIBRARY_API_KEY", "must-not-propagate")
    env_file = _credential_file(
        tmp_path,
        "# local ignored credential\n\nCDISC_LIBRARY_API_KEY=file-key-value\n",
    )
    captured = {}

    def fake_run(command, **kwargs):
        captured["command"] = command
        captured["kwargs"] = kwargs
        return subprocess.CompletedProcess(command, 0)

    with patch.object(run_core_update_cache.subprocess, "run", side_effect=fake_run):
        result = run_core_update_cache.main(
            _arguments(env_file),
            stdin=io.BytesIO(b"inherited-key-value"),
        )

    assert result == 0
    assert captured["command"] == [
        "/controlled/python",
        "-E",
        "-s",
        "-B",
        "/controlled/core.py",
        "update-cache",
        "-c",
        "/controlled/cache",
    ]
    child_environment = captured["kwargs"]["env"]
    assert child_environment["CDISC_LIBRARY_API_KEY"] == "file-key-value"
    assert "TROPIC_INHERITED_CDISC_LIBRARY_API_KEY" not in child_environment
    assert captured["kwargs"]["stdin"] is subprocess.DEVNULL
    assert captured["kwargs"]["stdout"] is subprocess.DEVNULL
    assert "shell" not in captured["kwargs"]
    output = capsys.readouterr()
    assert "file-key-value" not in output.out + output.err
    assert "inherited-key-value" not in output.out + output.err


def test_wrapper_uses_literal_allowlist_for_credential_child(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("CDISC_LIBRARY_API_KEY", raising=False)
    monkeypatch.setenv("PYTHONPATH", str(tmp_path / "inject"))
    monkeypatch.setenv("PYTHONHOME", str(tmp_path / "fake-home"))
    monkeypatch.setenv("DYLD_INSERT_LIBRARIES", str(tmp_path / "inject.dylib"))
    monkeypatch.setenv("LD_PRELOAD", str(tmp_path / "inject.so"))
    monkeypatch.setenv("LD_AUDIT", str(tmp_path / "audit.so"))
    monkeypatch.setenv("VIRTUAL_ENV", str(tmp_path / "old-venv"))
    monkeypatch.setenv("HTTPS_PROXY", "https://127.0.0.1:4443")
    monkeypatch.setenv("ALL_PROXY", "socks5://127.0.0.1:4444")
    monkeypatch.setenv("REQUESTS_CA_BUNDLE", str(tmp_path / "attacker-ca.pem"))
    monkeypatch.setenv("CURL_CA_BUNDLE", str(tmp_path / "attacker-ca.pem"))
    monkeypatch.setenv("SSL_CERT_FILE", str(tmp_path / "attacker-ca.pem"))
    monkeypatch.setenv("NETRC", str(tmp_path / "attacker-netrc"))
    monkeypatch.setenv("HOME", str(tmp_path / "attacker-home"))
    monkeypatch.setenv("TROPIC_UNRELATED_SENTINEL", "must-not-propagate")
    captured = {}

    def fake_run(command, **kwargs):
        captured["command"] = command
        captured["environment"] = kwargs["env"]
        return subprocess.CompletedProcess(command, 0)

    with patch.object(run_core_update_cache.subprocess, "run", side_effect=fake_run):
        result = run_core_update_cache.main(
            _arguments(tmp_path / "missing.env"),
            stdin=io.BytesIO(b"fake-nonsecret-key"),
        )

    assert result == 0
    assert captured["command"][1:4] == ["-E", "-s", "-B"]
    environment = captured["environment"]
    assert environment == {
        "CDISC_LIBRARY_API_KEY": "fake-nonsecret-key",
        "PATH": os.defpath,
        "LANG": "C",
        "LC_ALL": "C",
        "TZ": "UTC",
    }


def test_inherited_pythonpath_cannot_execute_with_child_credential(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("CDISC_LIBRARY_API_KEY", raising=False)
    injection_dir = tmp_path / "injection"
    injection_dir.mkdir()
    marker = tmp_path / "injected-code-ran"
    (injection_dir / "rogue.py").write_text(
        "import os\n"
        "from pathlib import Path\n"
        "Path(os.environ['TROPIC_TEST_MARKER']).write_text("
        "str('CDISC_LIBRARY_API_KEY' in os.environ), encoding='utf-8')\n",
        encoding="utf-8",
    )
    core = tmp_path / "fake_core.py"
    core.write_text(
        "try:\n"
        "    import rogue  # noqa: F401\n"
        "except ModuleNotFoundError:\n"
        "    raise SystemExit(0)\n"
        "raise SystemExit(9)\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("PYTHONPATH", str(injection_dir))
    monkeypatch.setenv("TROPIC_TEST_MARKER", str(marker))

    result = run_core_update_cache.main(
        [
            str(tmp_path / "missing.env"),
            os.fsdecode(os.path.realpath(sys.executable)),
            str(core),
            str(tmp_path / "cache"),
        ],
        stdin=io.BytesIO(b"fake-nonsecret-key"),
    )

    assert result == 0
    assert not marker.exists()


def test_wrapper_preserves_inherited_key_when_env_file_is_absent(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("CDISC_LIBRARY_API_KEY", raising=False)
    captured = {}

    def fake_run(command, **kwargs):
        captured.update(kwargs)
        return subprocess.CompletedProcess(command, 0)

    with patch.object(run_core_update_cache.subprocess, "run", side_effect=fake_run):
        result = run_core_update_cache.main(
            _arguments(tmp_path / "missing.env"),
            stdin=io.BytesIO(b"inherited-key-value"),
        )
    assert result == 0
    assert captured["env"]["CDISC_LIBRARY_API_KEY"] == "inherited-key-value"


def test_wrapper_rejects_symlinked_env_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.delenv("CDISC_LIBRARY_API_KEY", raising=False)
    target = _credential_file(tmp_path, "CDISC_LIBRARY_API_KEY=external-key\n")
    link = tmp_path / "linked.env"
    link.symlink_to(target)
    with patch.object(run_core_update_cache.subprocess, "run") as launch:
        result = run_core_update_cache.main(
            _arguments(link),
            stdin=io.BytesIO(b"inherited-key-value"),
        )
    assert result == 2
    launch.assert_not_called()
    output = capsys.readouterr()
    assert "without following links" in output.err
    assert "external-key" not in output.err


def test_wrapper_rejects_symlinked_env_directory(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("CDISC_LIBRARY_API_KEY", raising=False)
    actual = tmp_path / "actual-run"
    actual.mkdir()
    env_file = _credential_file(actual, "CDISC_LIBRARY_API_KEY=external-key\n")
    linked = tmp_path / "linked-run"
    linked.symlink_to(actual, target_is_directory=True)
    with patch.object(run_core_update_cache.subprocess, "run") as launch:
        result = run_core_update_cache.main(
            _arguments(linked / env_file.name),
            stdin=io.BytesIO(b"inherited-key-value"),
        )
    assert result == 2
    launch.assert_not_called()


@pytest.mark.parametrize("mode", [0o400, 0o640, 0o644, 0o660])
def test_wrapper_requires_exact_mode_0600(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    mode: int,
) -> None:
    monkeypatch.delenv("CDISC_LIBRARY_API_KEY", raising=False)
    env_file = _credential_file(
        tmp_path,
        "CDISC_LIBRARY_API_KEY=file-key-value\n",
        mode=mode,
    )
    with patch.object(run_core_update_cache.subprocess, "run") as launch:
        result = run_core_update_cache.main(
            _arguments(env_file),
            stdin=io.BytesIO(b""),
        )
    assert result == 2
    launch.assert_not_called()


@pytest.mark.parametrize(
    "content",
    [
        "# comments are not a credential\n",
        "export CDISC_LIBRARY_API_KEY=value\n",
        "OTHER_KEY=value\n",
        "CDISC_LIBRARY_API_KEY=\n",
        "CDISC_LIBRARY_API_KEY=one\nCDISC_LIBRARY_API_KEY=two\n",
        "CDISC_LIBRARY_API_KEY=one\necho arbitrary-shell\n",
    ],
)
def test_wrapper_rejects_malformed_or_ambiguous_env_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    content: str,
) -> None:
    monkeypatch.delenv("CDISC_LIBRARY_API_KEY", raising=False)
    env_file = _credential_file(tmp_path, content)
    with patch.object(run_core_update_cache.subprocess, "run") as launch:
        result = run_core_update_cache.main(
            _arguments(env_file),
            stdin=io.BytesIO(b"inherited-key-value"),
        )
    assert result == 2
    launch.assert_not_called()


def test_wrapper_rejects_oversized_env_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("CDISC_LIBRARY_API_KEY", raising=False)
    env_file = _credential_file(
        tmp_path,
        "CDISC_LIBRARY_API_KEY=" + "x" * run_core_update_cache.MAX_CREDENTIAL_BYTES,
    )
    with patch.object(run_core_update_cache.subprocess, "run") as launch:
        result = run_core_update_cache.main(
            _arguments(env_file),
            stdin=io.BytesIO(b""),
        )
    assert result == 2
    launch.assert_not_called()


@pytest.mark.skipif(not hasattr(os, "mkfifo"), reason="POSIX FIFO required")
def test_wrapper_rejects_nonregular_env_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("CDISC_LIBRARY_API_KEY", raising=False)
    env_file = tmp_path / ".env"
    os.mkfifo(env_file, mode=0o600)
    with patch.object(run_core_update_cache.subprocess, "run") as launch:
        result = run_core_update_cache.main(
            _arguments(env_file),
            stdin=io.BytesIO(b""),
        )
    assert result == 2
    launch.assert_not_called()


def test_wrapper_rejects_wrong_owner_before_parsing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("CDISC_LIBRARY_API_KEY", raising=False)
    env_file = _credential_file(tmp_path, "CDISC_LIBRARY_API_KEY=file-key-value\n")
    current_uid = os.getuid()
    monkeypatch.setattr(run_core_update_cache.os, "getuid", lambda: current_uid + 1)
    with patch.object(run_core_update_cache.subprocess, "run") as launch:
        result = run_core_update_cache.main(
            _arguments(env_file),
            stdin=io.BytesIO(b""),
        )
    assert result == 2
    launch.assert_not_called()


def test_wrapper_rejects_key_in_its_own_environment(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("CDISC_LIBRARY_API_KEY", "must-not-enter-wrapper")
    with patch.object(run_core_update_cache.subprocess, "run") as launch:
        result = run_core_update_cache.main(
            _arguments(tmp_path / "missing.env"),
            stdin=io.BytesIO(b"inherited-key-value"),
        )
    assert result == 2
    launch.assert_not_called()
