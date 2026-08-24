"""Fail-closed tests for the independently hashed CDISC CORE custom rules."""

from __future__ import annotations

import hashlib
import json
import os
import re
import stat
import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "platform/run_core_conformance.sh"
RULE_DIR = ROOT / "platform/conformance_rules/adam"
LOCK_PATH = RULE_DIR / "RULES.lock"
RULE_NAMES = tuple(f"TROPIC-ADAM-{number}.yml" for number in range(101, 108))


def _verifier_source() -> str:
    runner = RUNNER.read_text(encoding="utf-8")
    match = re.search(
        r"<<'PY_CORE_RULE_LOCK'\n(.*?)\nPY_CORE_RULE_LOCK",
        runner,
        flags=re.DOTALL,
    )
    assert match, "CORE rule-lock verifier heredoc is missing"
    return match.group(1)


def _write_synthetic_tree(root: Path) -> Path:
    rule_dir = root / "platform/conformance_rules/adam"
    rule_dir.mkdir(parents=True)
    rows = []
    for name in RULE_NAMES:
        content = f"id: {name.removesuffix('.yml')}\n".encode()
        (rule_dir / name).write_bytes(content)
        rows.append({"path": name, "sha256": hashlib.sha256(content).hexdigest()})
    payload = {
        "schema": "tropic-core-custom-rule-lock/v1",
        "algorithm": "sha256",
        "rules": rows,
    }
    (rule_dir / "RULES.lock").write_text(
        json.dumps(payload, indent=2) + "\n",
        encoding="utf-8",
    )
    return rule_dir


def _run_verifier(root: Path, *, credential_present: bool = False):
    environment = {
        key: os.environ[key]
        for key in os.environ
        if key != "CDISC_LIBRARY_API_KEY"
    }
    if credential_present:
        environment["CDISC_LIBRARY_API_KEY"] = "synthetic-test-value"
    return subprocess.run(
        [sys.executable, "-I", "-S", "-", str(root)],
        input=_verifier_source(),
        text=True,
        capture_output=True,
        env=environment,
        check=False,
    )


def test_tracked_core_rule_lock_matches_exact_current_yaml_set() -> None:
    payload = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
    assert set(payload) == {"schema", "algorithm", "rules"}
    assert payload["schema"] == "tropic-core-custom-rule-lock/v1"
    assert payload["algorithm"] == "sha256"
    assert tuple(row["path"] for row in payload["rules"]) == RULE_NAMES
    assert set(path.name for path in RULE_DIR.iterdir()) == {*RULE_NAMES, "RULES.lock"}
    for row in payload["rules"]:
        path = RULE_DIR / row["path"]
        metadata = path.lstat()
        assert stat.S_ISREG(metadata.st_mode)
        assert not path.is_symlink()
        assert hashlib.sha256(path.read_bytes()).hexdigest() == row["sha256"]


def test_runner_verifies_rules_credential_free_before_install_and_core() -> None:
    runner = RUNNER.read_text(encoding="utf-8")
    calls = [match.start() for match in re.finditer(r"(?m)^verify_core_rules$", runner)]
    assert len(calls) == 2
    capture = runner.index(
        'TROPIC_INHERITED_CDISC_LIBRARY_API_KEY="${CDISC_LIBRARY_API_KEY-}"'
    )
    initial_unset = runner.index("unset CDISC_LIBRARY_API_KEY", capture)
    install = runner.index('"$PY" -I -m pip install', calls[0])
    clone = runner.index("git clone", install)
    update_cache = runner.index(
        '"$PY" -I -S "$ROOT/platform/run_core_update_cache.py"', clone
    )
    final_unset = runner.index("unset TROPIC_INHERITED_CDISC_LIBRARY_API_KEY", update_cache)
    adam_core = runner.index('"$PY" -E -s -B "$CORE" validate -s adamig', calls[1])
    assert initial_unset < calls[0] < install < clone < update_cache
    assert update_cache < final_unset < calls[1] < adam_core
    assert "env -i" in runner
    assert "clean_env python3 -I -S -" in runner
    assert "python3 -I -S - \"$ROOT\"" in runner
    assert 'export -n TROPIC_INHERITED_CDISC_LIBRARY_API_KEY' in runner
    assert '-lr "$RULES_DIR"' in runner


def test_core_rule_verifier_accepts_exact_regular_files(tmp_path: Path) -> None:
    _write_synthetic_tree(tmp_path)
    result = _run_verifier(tmp_path)
    assert result.returncode == 0, result.stderr


def test_core_rule_verifier_rejects_missing_rule(tmp_path: Path) -> None:
    rule_dir = _write_synthetic_tree(tmp_path)
    (rule_dir / RULE_NAMES[0]).unlink()
    result = _run_verifier(tmp_path)
    assert result.returncode != 0
    assert "missing entries" in result.stderr


def test_core_rule_verifier_rejects_extra_core_rule(tmp_path: Path) -> None:
    rule_dir = _write_synthetic_tree(tmp_path)
    (rule_dir / "unlocked-rule.json").write_text("{}\n", encoding="utf-8")
    result = _run_verifier(tmp_path)
    assert result.returncode != 0
    assert "extra entries" in result.stderr


def test_core_rule_verifier_rejects_rule_symlink(tmp_path: Path) -> None:
    rule_dir = _write_synthetic_tree(tmp_path)
    rule = rule_dir / RULE_NAMES[0]
    external = tmp_path / "external-rule.yml"
    external.write_bytes(rule.read_bytes())
    rule.unlink()
    rule.symlink_to(external)
    result = _run_verifier(tmp_path)
    assert result.returncode != 0
    assert "without following links" in result.stderr


@pytest.mark.skipif(not hasattr(os, "mkfifo"), reason="POSIX FIFO required")
def test_core_rule_verifier_rejects_nonregular_rule(tmp_path: Path) -> None:
    rule_dir = _write_synthetic_tree(tmp_path)
    rule = rule_dir / RULE_NAMES[0]
    rule.unlink()
    os.mkfifo(rule)
    result = _run_verifier(tmp_path)
    assert result.returncode != 0
    assert "not a regular file" in result.stderr


def test_core_rule_verifier_rejects_symlinked_lock(tmp_path: Path) -> None:
    rule_dir = _write_synthetic_tree(tmp_path)
    lock = rule_dir / "RULES.lock"
    external = tmp_path / "external.lock"
    lock.replace(external)
    lock.symlink_to(external)
    result = _run_verifier(tmp_path)
    assert result.returncode != 0
    assert "without following links" in result.stderr


def test_core_rule_verifier_rejects_symlinked_rule_directory(tmp_path: Path) -> None:
    rule_dir = _write_synthetic_tree(tmp_path)
    external = tmp_path / "external-adam-rules"
    rule_dir.replace(external)
    rule_dir.symlink_to(external, target_is_directory=True)
    result = _run_verifier(tmp_path)
    assert result.returncode != 0
    assert "ancestor is not a real directory" in result.stderr


def test_core_rule_verifier_rejects_hash_mismatch(tmp_path: Path) -> None:
    rule_dir = _write_synthetic_tree(tmp_path)
    (rule_dir / RULE_NAMES[0]).write_text("changed: true\n", encoding="utf-8")
    result = _run_verifier(tmp_path)
    assert result.returncode != 0
    assert "SHA-256 mismatch" in result.stderr


def test_core_rule_verifier_refuses_credential_bearing_environment(
    tmp_path: Path,
) -> None:
    _write_synthetic_tree(tmp_path)
    result = _run_verifier(tmp_path, credential_present=True)
    assert result.returncode != 0
    assert "must run without CDISC_LIBRARY_API_KEY" in result.stderr
