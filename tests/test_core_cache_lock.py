from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "platform"))

import verify_core_cache as cache_lock  # noqa: E402


def test_cache_lock_round_trip_and_drift_detection(tmp_path: Path) -> None:
    cache = tmp_path / "cache"
    cache.mkdir()
    (cache / "rules.pkl").write_bytes(b"rules-v1")
    (cache / "sdtmct-2026-03-27.pkl").write_bytes(b"ct-v1")
    manifest = tmp_path / "core_cache_manifest.json"

    assert cache_lock.main(
        ["--cache", str(cache), "--manifest", str(manifest), "--write"]
    ) == 0
    assert cache_lock.main(
        ["--cache", str(cache), "--manifest", str(manifest)]
    ) == 0

    (cache / "rules.pkl").write_bytes(b"rules-v2")
    assert cache_lock.main(
        ["--cache", str(cache), "--manifest", str(manifest)]
    ) == 1


def test_initial_empty_cache_allowance_is_narrow(tmp_path: Path) -> None:
    cache = tmp_path / "cache"
    cache.mkdir()
    manifest = tmp_path / "core_cache_manifest.json"

    assert cache_lock.main(
        [
            "--cache",
            str(cache),
            "--manifest",
            str(manifest),
            "--allow-initial-empty-cache",
        ]
    ) == 0
    assert cache_lock.main(
        ["--cache", str(cache), "--manifest", str(manifest)]
    ) == 1


def test_cache_lock_rejects_symlink_entry(tmp_path: Path) -> None:
    cache = tmp_path / "cache"
    cache.mkdir()
    outside = tmp_path / "outside.pkl"
    outside.write_bytes(b"outside")
    (cache / "rules.pkl").symlink_to(outside)

    try:
        cache_lock.build_inventory(cache)
    except (cache_lock.CacheLockError, OSError):
        pass
    else:  # pragma: no cover - assertion branch
        raise AssertionError("symlink cache entry was accepted")


def test_cache_lock_rejects_symlink_cache_ancestor(tmp_path: Path) -> None:
    real_parent = tmp_path / "real-parent"
    cache = real_parent / "cache"
    cache.mkdir(parents=True)
    (cache / "rules.pkl").write_bytes(b"outside")
    linked_parent = tmp_path / "linked-parent"
    linked_parent.symlink_to(real_parent, target_is_directory=True)

    try:
        cache_lock.build_inventory(linked_parent / "cache")
    except (cache_lock.CacheLockError, OSError):
        pass
    else:  # pragma: no cover - assertion branch
        raise AssertionError("symlink cache ancestor was accepted")


def test_cache_lock_write_rejects_symlink_manifest(tmp_path: Path) -> None:
    cache = tmp_path / "cache"
    cache.mkdir()
    (cache / "rules.pkl").write_bytes(b"synthetic")
    victim = tmp_path / "victim.txt"
    victim.write_text("DO-NOT-CHANGE", encoding="utf-8")
    manifest = tmp_path / "core_cache_manifest.json"
    manifest.symlink_to(victim)

    assert cache_lock.main(
        ["--cache", str(cache), "--manifest", str(manifest), "--write"]
    ) == 1
    assert victim.read_text(encoding="utf-8") == "DO-NOT-CHANGE"


def test_cache_lock_write_rejects_symlink_parent(tmp_path: Path) -> None:
    cache = tmp_path / "cache"
    cache.mkdir()
    (cache / "rules.pkl").write_bytes(b"synthetic")
    real_parent = tmp_path / "real-parent"
    real_parent.mkdir()
    linked_parent = tmp_path / "linked-parent"
    linked_parent.symlink_to(real_parent, target_is_directory=True)
    manifest = linked_parent / "core_cache_manifest.json"

    assert cache_lock.main(
        ["--cache", str(cache), "--manifest", str(manifest), "--write"]
    ) == 1
    assert not (real_parent / "core_cache_manifest.json").exists()


def test_cache_lock_read_rejects_symlink_manifest_parent(tmp_path: Path) -> None:
    cache = tmp_path / "cache"
    cache.mkdir()
    (cache / "rules.pkl").write_bytes(b"synthetic")
    real_parent = tmp_path / "real-parent"
    real_parent.mkdir()
    real_manifest = real_parent / "core_cache_manifest.json"
    assert cache_lock.main(
        ["--cache", str(cache), "--manifest", str(real_manifest), "--write"]
    ) == 0
    linked_parent = tmp_path / "linked-parent"
    linked_parent.symlink_to(real_parent, target_is_directory=True)

    assert cache_lock.main(
        [
            "--cache",
            str(cache),
            "--manifest",
            str(linked_parent / real_manifest.name),
        ]
    ) == 1


def test_initial_empty_cache_rejects_symlink_ancestor(tmp_path: Path) -> None:
    real_parent = tmp_path / "real-parent"
    cache = real_parent / "cache"
    cache.mkdir(parents=True)
    linked_parent = tmp_path / "linked-parent"
    linked_parent.symlink_to(real_parent, target_is_directory=True)

    assert cache_lock.main(
        [
            "--cache",
            str(linked_parent / "cache"),
            "--manifest",
            str(tmp_path / "manifest.json"),
            "--allow-initial-empty-cache",
        ]
    ) == 1


def test_cache_lock_rejects_fifo_without_blocking(tmp_path: Path) -> None:
    cache = tmp_path / "cache"
    cache.mkdir()
    os.mkfifo(cache / "rules.pkl")
    manifest = tmp_path / "core_cache_manifest.json"

    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "platform/verify_core_cache.py"),
            "--cache",
            str(cache),
            "--manifest",
            str(manifest),
        ],
        capture_output=True,
        text=True,
        timeout=3,
        check=False,
    )
    assert result.returncode == 1
    assert "cache entry is not regular" in result.stderr


def test_committed_cache_manifest_is_structurally_valid() -> None:
    manifest = ROOT / "platform/conformance/core_cache_manifest.json"
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    cache_lock._validate_shape(payload)
    assert payload["file_count"] >= 6
    assert {"rules.pkl", "standards_models.pkl", "variables_metadata.pkl"} <= {
        row["path"] for row in payload["files"]
    }


def test_core_runner_verifies_cache_before_refresh_and_validation() -> None:
    runner = (ROOT / "platform/run_core_conformance.sh").read_text(encoding="utf-8")
    pre_verify = runner.index("verify_core_cache.py")
    update = runner.index("run_core_update_cache.py", pre_verify)
    post_verify = runner.index("verify_core_cache.py", update)
    first_validation = runner.index('"$PY" -E -s -B "$CORE" validate', post_verify)
    assert pre_verify < update < post_verify < first_validation
    assert "--allow-initial-empty-cache" in runner[pre_verify:update]
    assert "--allow-initial-empty-cache" not in runner[post_verify:first_validation]
    assert "--write" not in runner
