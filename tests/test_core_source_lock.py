from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "platform"))

import verify_core_source as source_lock  # noqa: E402


BASE_STANDARD_TYPES = '''class StandardTypes:
    ADAM = "adam"
    TIG = "tig"
'''


def _git(repo: Path, *args: str) -> str:
    return subprocess.check_output(
        ["git", "-C", str(repo), *args], text=True
    ).strip()


def _engine_repo(tmp_path: Path) -> tuple[Path, str]:
    engine = tmp_path / "engine"
    standard_types = engine / source_lock.PATCH_PATH
    standard_types.parent.mkdir(parents=True)
    standard_types.write_text(BASE_STANDARD_TYPES, encoding="utf-8")
    (engine / "core.py").write_text("print('core')\n", encoding="utf-8")
    (engine / ".gitignore").write_text("__pycache__/\n*.pyc\n", encoding="utf-8")
    cache = engine / "resources/cache"
    cache.mkdir(parents=True)
    (cache / "rules.pkl").write_bytes(b"rules-v1")
    subprocess.run(["git", "init", "-q", str(engine)], check=True)
    _git(engine, "config", "user.email", "test@example.invalid")
    _git(engine, "config", "user.name", "TROPIC Test")
    _git(engine, "add", ".")
    _git(engine, "commit", "-q", "-m", "fixture")
    return engine, _git(engine, "rev-parse", "HEAD")


def test_source_lock_applies_only_deterministic_compatibility_patch(
    tmp_path: Path,
) -> None:
    engine, commit = _engine_repo(tmp_path)
    assert source_lock.main(["--engine", str(engine), "--commit", commit]) == 0
    patched = (engine / source_lock.PATCH_PATH).read_bytes()
    assert source_lock.PATCHED_BLOCK in patched
    assert source_lock.main(["--engine", str(engine), "--commit", commit]) == 0


def test_source_lock_rejects_other_tracked_source_drift(tmp_path: Path) -> None:
    engine, commit = _engine_repo(tmp_path)
    assert source_lock.main(["--engine", str(engine), "--commit", commit]) == 0
    (engine / "core.py").write_text("print('changed')\n", encoding="utf-8")
    assert source_lock.main(["--engine", str(engine), "--commit", commit]) == 1


def test_source_lock_rejects_untracked_executable_source(tmp_path: Path) -> None:
    engine, commit = _engine_repo(tmp_path)
    assert source_lock.main(["--engine", str(engine), "--commit", commit]) == 0
    (engine / "rogue.py").write_text("raise SystemExit\n", encoding="utf-8")
    assert source_lock.main(["--engine", str(engine), "--commit", commit]) == 1


def test_source_lock_allows_separately_governed_cache_drift(tmp_path: Path) -> None:
    engine, commit = _engine_repo(tmp_path)
    assert source_lock.main(["--engine", str(engine), "--commit", commit]) == 0
    (engine / "resources/cache/rules.pkl").write_bytes(b"rules-v2")
    assert source_lock.main(["--engine", str(engine), "--commit", commit]) == 0


def test_source_lock_rejects_assume_unchanged_tracked_drift(tmp_path: Path) -> None:
    engine, commit = _engine_repo(tmp_path)
    assert source_lock.main(["--engine", str(engine), "--commit", commit]) == 0
    (engine / "core.py").write_text("raise RuntimeError('hidden')\n", encoding="utf-8")
    _git(engine, "update-index", "--assume-unchanged", "core.py")

    assert source_lock.main(["--engine", str(engine), "--commit", commit]) == 1


def test_source_lock_rejects_skip_worktree_tracked_drift(tmp_path: Path) -> None:
    engine, commit = _engine_repo(tmp_path)
    assert source_lock.main(["--engine", str(engine), "--commit", commit]) == 0
    _git(engine, "update-index", "--skip-worktree", "core.py")
    (engine / "core.py").write_text("raise RuntimeError('hidden')\n", encoding="utf-8")

    assert source_lock.main(["--engine", str(engine), "--commit", commit]) == 1


def test_source_lock_rejects_ignored_python_bytecode(tmp_path: Path) -> None:
    engine, commit = _engine_repo(tmp_path)
    assert source_lock.main(["--engine", str(engine), "--commit", commit]) == 0
    bytecode = engine / "__pycache__/rogue.cpython-312.pyc"
    bytecode.parent.mkdir()
    bytecode.write_bytes(b"unreviewed-bytecode")

    assert source_lock.main(["--engine", str(engine), "--commit", commit]) == 1


def test_source_lock_rejects_ancestor_symlink_without_modifying_target(
    tmp_path: Path,
) -> None:
    engine, commit = _engine_repo(tmp_path)
    package = engine / "cdisc_rules_engine"
    outside_package = tmp_path / "outside-package"
    shutil.copytree(package, outside_package)
    victim = outside_package / "enums/standard_types.py"
    before = victim.read_bytes()
    shutil.rmtree(package)
    package.symlink_to(outside_package, target_is_directory=True)

    assert source_lock.main(["--engine", str(engine), "--commit", commit]) == 1
    assert victim.read_bytes() == before
