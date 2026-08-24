#!/usr/bin/env python3
"""Rebind an existing real-SAS health snapshot after governance-only changes.

This does not rerun SAS, regenerate datasets, or change a clinical result. It is
valid only for a clean committed tree containing reviewer-facing documentation or
presentation changes. Executor, inventory, verifier, CI, dependency, regulatory-
gate, and governing-test changes require a fresh genuine run. The supplied base
must independently rehash to the source digest carried by pipeline_health.json.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath


ROOT = Path(__file__).resolve().parents[1]
HEALTH = ROOT / "platform/pipeline_health.json"
HEALTH_REL = "platform/pipeline_health.json"
BASE_MANIFEST_REL = "platform/release_run_manifest/release_run_manifest.json"

sys.path.insert(0, str(ROOT / "platform"))
from governance_reseal_policy import (  # noqa: E402
    RESEALABLE_EXACT_PATHS,
    governance_chain_policy_problems,
    is_resealable_path,
)
from safe_filesystem import atomic_write_json  # noqa: E402

# Governance-only resealing is deliberately limited to reviewer-facing prose and
# presentation evidence. Executable controls, inventories, dependencies, status
# files, tests, and release authority code require a fresh genuine SAS run (or an
# independently controlled release approval outside this repository).
ALLOWED_PATHS = RESEALABLE_EXACT_PATHS

# Kept explicit both as executable policy documentation and as a regression-test
# target. The documentation allowlist already rejects these paths; this registry
# makes the trust boundary unmistakable when new controls are added.
FRESH_RUN_REQUIRED_PATHS = frozenset({
    "00_governance/REPRODUCIBILITY.md",
    ".github/CODEOWNERS",
    ".github/workflows/ci.yml",
    ".gitleaks.toml",
    ".pre-commit-config.yaml",
    "config/regulatory_baseline.yaml",
    "config/regulatory_source_inventory.yaml",
    "config/study_manifest.yaml",
    "docs/PRODUCT_CLAIM.md",
    "docs/QUALITY_SYSTEM_BOUNDARY.md",
    "docs/RELEASE_NOTE_v0.3.0-clinical-simulation.md",
    "platform/build_release_run_manifest.py",
    "platform/build_release_candidate_checklist.py",
    "platform/check_regulatory_baseline.py",
    "platform/cibuild.py",
    "requirements-core-build.lock",
    "requirements-core.txt",
    "requirements-core.lock",
    "requirements-ci-build.lock",
    "requirements-ci.txt",
    "requirements-ci.lock",
    "renv.lock",
    "scripts/rebind_governance_seal.py",
    "scripts/verify_release.py",
})
FRESH_RUN_REQUIRED_PREFIXES = (".github/", "platform/", "scripts/", "tests/")


def _run_git(args: list[str], *, text: bool = True):
    return subprocess.check_output(
        ["git", *args],
        cwd=ROOT,
        text=text,
        stderr=subprocess.DEVNULL,
    )


def _changed_paths(base: str, head: str = "HEAD") -> list[str]:
    output = _run_git(["diff", "--name-only", f"{base}..{head}", "--"])
    return [line.strip() for line in output.splitlines() if line.strip()]


def _is_allowed(path: str) -> bool:
    return is_resealable_path(path)


def _requires_fresh_run(path: str) -> bool:
    return path in FRESH_RUN_REQUIRED_PATHS or any(
        path.startswith(prefix) for prefix in FRESH_RUN_REQUIRED_PREFIXES
    )


def _material_worktree_changes() -> list[str]:
    """Return staged, unstaged, and untracked paths before source sealing."""
    output = _run_git(
        ["status", "--porcelain=v1", "--untracked-files=all", "--ignore-submodules=none"]
    )
    return [line for line in output.splitlines() if line]


def _resolve_commit(revision: str) -> str:
    if not revision or revision.strip() != revision or "\n" in revision:
        raise ValueError("base revision is empty or malformed")
    try:
        return _run_git(["rev-parse", "--verify", f"{revision}^{{commit}}"]).strip()
    except (OSError, subprocess.CalledProcessError) as exc:
        raise ValueError(f"base revision is not a commit: {revision}") from exc


def _is_ancestor(base: str, head: str) -> bool:
    try:
        subprocess.check_call(
            ["git", "merge-base", "--is-ancestor", base, head],
            cwd=ROOT,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return True
    except (OSError, subprocess.CalledProcessError):
        return False


def _safe_manifest_path(path: str) -> bool:
    if not path or "\\" in path or ":" in path or "\x00" in path:
        return False
    parsed = PurePosixPath(path)
    return not parsed.is_absolute() and ".." not in parsed.parts and path != "."


def _git_blob(revision: str, path: str) -> bytes:
    if not _safe_manifest_path(path):
        raise ValueError(f"unsafe path in base release manifest: {path!r}")
    try:
        return _run_git(["cat-file", "blob", f"{revision}:{path}"], text=False)
    except (OSError, subprocess.CalledProcessError) as exc:
        raise ValueError(f"base release manifest path is missing: {path}") from exc


def _git_json(revision: str, path: str) -> dict:
    try:
        data = json.loads(_git_blob(revision, path).decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"base {path} is not valid UTF-8 JSON") from exc
    if not isinstance(data, dict):
        raise ValueError(f"base {path} is not a JSON object")
    return data


def _manifest_sha256(manifest: dict) -> str:
    unsigned = dict(manifest)
    unsigned.pop("manifest_sha256", None)
    payload = json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _source_rows_sha256(rows: list[tuple[str, str]]) -> str:
    encoded = b"\n".join(
        f"{path}\0{digest}".encode("utf-8") for path, digest in sorted(rows)
    )
    return hashlib.sha256(encoded).hexdigest()


def _sealed_source_registry(revision: str) -> tuple[dict, list[tuple[str, str]]]:
    """Return a self-sealed manifest and its validated source registry."""
    manifest = _git_json(revision, BASE_MANIFEST_REL)
    recorded_seal = str(manifest.get("manifest_sha256") or "")
    if not recorded_seal or recorded_seal != _manifest_sha256(manifest):
        raise ValueError("base release manifest self-seal is invalid")

    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, dict):
        raise ValueError("base release manifest has no artifact registry")

    source_rows: list[tuple[str, str]] = []
    for group in ("controls", "programs"):
        rows = artifacts.get(group)
        if not isinstance(rows, list) or not rows:
            raise ValueError(f"base release manifest {group} registry is missing")
        seen: set[str] = set()
        for row in rows:
            if not isinstance(row, dict):
                raise ValueError(f"base release manifest {group} row is malformed")
            path = str(row.get("path") or "")
            expected = str(row.get("sha256") or "")
            if path in seen:
                raise ValueError(f"base release manifest {group} duplicates {path}")
            seen.add(path)
            if (
                len(expected) != 64
                or any(ch not in "0123456789abcdef" for ch in expected)
                or row.get("present") is not True
            ):
                raise ValueError(f"base release manifest has invalid source row: {path!r}")
            actual = hashlib.sha256(_git_blob(revision, path)).hexdigest()
            if actual != expected:
                raise ValueError(f"base source does not match its release manifest: {path}")
            source_rows.append((path, expected))

    computed = _source_rows_sha256(source_rows)
    recorded = str((manifest.get("source_control") or {}).get("source_tree_sha256") or "")
    if not recorded or computed != recorded:
        raise ValueError("base release manifest source-tree digest is invalid")
    return manifest, source_rows


def _source_digest_at_revision(revision: str) -> str:
    """Rehash a base manifest's source registries directly from committed blobs."""
    _, rows = _sealed_source_registry(revision)
    return _source_rows_sha256(rows)


def _source_digest_for_committed_head(base_revision: str, head_revision: str) -> str:
    """Hash HEAD blobs using the authenticated base run's exact source inventory.

    The governance allowlist cannot change the manifest builder or add/remove a
    program, so this registry is stable across an eligible reseal.  Reading Git
    blobs rather than mutable working-tree paths closes the status-check/hash
    race and excludes ignored files by construction.
    """
    _, base_rows = _sealed_source_registry(base_revision)
    head_rows = [
        (path, hashlib.sha256(_git_blob(head_revision, path)).hexdigest())
        for path, _ in base_rows
    ]
    return _source_rows_sha256(head_rows)


def _verify_manifest_health_binding(revision: str, health: dict) -> None:
    """Require the sealed run manifest to authenticate the carried health blob."""
    manifest = _git_json(revision, BASE_MANIFEST_REL)
    recorded_seal = str(manifest.get("manifest_sha256") or "")
    if not recorded_seal or recorded_seal != _manifest_sha256(manifest):
        raise ValueError("base release manifest self-seal is invalid")

    environment = manifest.get("environment") or {}
    completeness = manifest.get("run_completeness") or {}
    if (
        health.get("pipeline_health_status") != "GREEN"
        or health.get("sas_execution_mode") not in {"oda", "local"}
        or health.get("run_scope") != "full_dag"
        or (health.get("provenance_guard") or {}).get("passed") is not True
        or environment.get("sas_execution_mode") != health.get("sas_execution_mode")
        or completeness.get("run_scope") != "full_dag"
        or completeness.get("health_run_scope") != "full_dag"
    ):
        raise ValueError("base manifest does not authenticate a genuine full-DAG run")

    artifacts = manifest.get("artifacts") or {}
    qc_rows = artifacts.get("qc_files") or []
    health_rows = [
        row for row in qc_rows
        if isinstance(row, dict) and row.get("path") == HEALTH_REL
    ]
    if len(health_rows) != 1 or health_rows[0].get("present") is not True:
        raise ValueError("base release manifest does not seal pipeline health")
    expected = str(health_rows[0].get("sha256") or "")
    actual = hashlib.sha256(_git_blob(revision, HEALTH_REL)).hexdigest()
    if expected != actual:
        raise ValueError("base release manifest pipeline-health seal is invalid")


def _authenticated_base_revision(
    requested: str,
    health: dict,
    *,
    head_revision: str | None = None,
) -> str:
    """Verify that the base commit is the exact source snapshot carried by health."""
    base = _resolve_commit(requested)
    head = head_revision or _resolve_commit("HEAD")
    if base == head:
        raise ValueError("base revision must predate the governance-only change")
    if not _is_ancestor(base, head):
        raise ValueError("base revision is not an ancestor of HEAD")

    base_health = _git_json(base, HEALTH_REL)
    if base_health != health:
        raise ValueError("base revision does not contain the carried pipeline health record")
    _verify_manifest_health_binding(base, base_health)
    expected = str(health.get("source_tree_sha256") or "")
    if not expected:
        raise ValueError("pipeline health has no source-tree digest")
    actual = _source_digest_at_revision(base)
    if actual != expected:
        raise ValueError(
            "base revision source tree does not match the carried genuine-run digest"
        )
    return base


def _governance_chain_policy_problems(health: dict) -> list[str]:
    """Compatibility wrapper around the shared fail-closed release policy."""
    return governance_chain_policy_problems(health)


def _health_change_is_prior_reseal_only(base: str) -> bool:
    """Allow health.json only when HEAD carries a valid prior reseal hop.

    A governance reseal necessarily updates pipeline_health.json. A second
    governance commit can therefore compare against a base before that hop and
    legitimately see the health file in the diff. Do not allow arbitrary health
    edits: the clinical timestamp/mode/status must match the base revision, the
    current chain must validate, and the last hop must end at the recorded source
    digest.
    """
    try:
        raw = subprocess.check_output(
            ["git", "show", f"{base}:platform/pipeline_health.json"],
            cwd=ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        )
        base_health = json.loads(raw)
        current_health = json.loads(HEALTH.read_text(encoding="utf-8"))
    except (subprocess.CalledProcessError, json.JSONDecodeError, OSError):
        return False
    return _health_is_valid_prior_reseal(base_health, current_health)


def _health_is_valid_prior_reseal(base_health: dict, current_health: dict) -> bool:
    """Validate a carried-forward health seal without requiring Git history."""
    for key in ("timestamp", "pipeline_health_status", "sas_execution_mode", "run_scope"):
        if current_health.get(key) != base_health.get(key):
            return False
    chain = current_health.get("governance_reseal_chain")
    if not isinstance(chain, list) or not chain or not all(isinstance(row, dict) for row in chain):
        return False
    expected = str(base_health.get("source_tree_sha256") or "")
    for row in chain:
        if (
            row.get("status") != "PASS"
            or row.get("clinical_run_was_not_reexecuted") is not True
            or row.get("prior_source_tree_sha256") != expected
        ):
            return False
        expected = str(row.get("rebound_source_tree_sha256") or "")
    return bool(expected) and expected == current_health.get("source_tree_sha256")


def _chain_from_base_revision(reseal: dict) -> list[dict]:
    """Recover an older append-only/legacy chain from the reseal's recorded base."""
    base = str(reseal.get("base_revision") or "")
    prior = str(reseal.get("prior_source_tree_sha256") or "")
    if not base or not prior:
        return []
    try:
        raw = subprocess.check_output(
            ["git", "show", f"{base}:platform/pipeline_health.json"],
            cwd=ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        )
        base_health = json.loads(raw)
    except (subprocess.CalledProcessError, json.JSONDecodeError, OSError):
        return []
    if base_health.get("source_tree_sha256") != prior:
        return []
    chain = base_health.get("governance_reseal_chain")
    if chain is None:
        legacy = base_health.get("governance_only_reseal")
        chain = [legacy] if isinstance(legacy, dict) else []
    if not isinstance(chain, list) or not all(isinstance(row, dict) for row in chain):
        return []
    if chain and chain[-1].get("rebound_source_tree_sha256") != prior:
        return []
    return chain


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "base_revision",
        help="committed release/run state whose sealed source digest is carried by pipeline health",
    )
    args = parser.parse_args(argv)

    head_revision = _resolve_commit("HEAD")
    dirty = _material_worktree_changes()
    if dirty:
        preview = ", ".join(dirty[:8])
        extra = "" if len(dirty) <= 8 else f" (+{len(dirty) - 8} more)"
        raise SystemExit(
            "refusing to hash a dirty source snapshot; commit or discard all changes first: "
            f"{preview}{extra}"
        )
    try:
        health = _git_json(head_revision, HEALTH_REL)
    except ValueError as exc:
        raise SystemExit(f"invalid committed pipeline health: {exc}") from exc
    if health.get("pipeline_health_status") != "GREEN":
        raise SystemExit("refusing to rebind a non-GREEN health snapshot")
    if health.get("sas_execution_mode") not in {"oda", "local"}:
        raise SystemExit("refusing to rebind a non-real-SAS health snapshot")
    if health.get("run_scope") != "full_dag":
        raise SystemExit("refusing to rebind a non-full-DAG health snapshot")
    if (health.get("provenance_guard") or {}).get("passed") is not True:
        raise SystemExit("refusing to rebind health without passed provenance guards")

    chain_problems = _governance_chain_policy_problems(health)
    if chain_problems:
        raise SystemExit(
            "carried governance reseal is invalid under the fresh-run policy: "
            + "; ".join(chain_problems)
        )
    try:
        base_revision = _authenticated_base_revision(
            args.base_revision,
            health,
            head_revision=head_revision,
        )
    except ValueError as exc:
        raise SystemExit(f"refusing unauthenticated governance base: {exc}") from exc

    changed = _changed_paths(base_revision, head_revision)
    disallowed = [path for path in changed if not _is_allowed(path)]
    if disallowed:
        critical = [path for path in disallowed if _requires_fresh_run(path)]
        detail = ", ".join(disallowed)
        if critical:
            detail += "; critical controls requiring a fresh genuine run: " + ", ".join(critical)
        raise SystemExit("non-documentation paths changed: " + detail)

    previous = health.get("source_tree_sha256") or ""
    try:
        rebound = _source_digest_for_committed_head(base_revision, head_revision)
    except ValueError as exc:
        raise SystemExit(f"unable to hash the committed source snapshot: {exc}") from exc
    if not previous or previous == rebound:
        raise SystemExit("source-tree rebind was unnecessary or had no prior digest")

    prior_reseal = health.get("governance_only_reseal")
    chain = health.get("governance_reseal_chain")
    if chain is None:
        chain = [prior_reseal] if isinstance(prior_reseal, dict) else []
    elif not isinstance(chain, list) or not all(isinstance(row, dict) for row in chain):
        raise SystemExit("refusing malformed governance_reseal_chain")
    if chain and chain[-1].get("rebound_source_tree_sha256") != previous:
        raise SystemExit("refusing discontinuous governance reseal chain")

    reseal = {
        "status": "PASS",
        "rebound_at": datetime.now(timezone.utc).isoformat(),
        "base_revision": base_revision,
        "clinical_run_timestamp": health.get("timestamp"),
        "prior_source_tree_sha256": previous,
        "rebound_source_tree_sha256": rebound,
        "changed_paths": changed,
        "clinical_run_was_not_reexecuted": True,
        "reason": (
            "Reviewer-facing documentation or presentation evidence changed; executor, "
            "manifest/inventory, verifier, reseal authority, CI/CODEOWNERS, dependencies, "
            "regulatory gates, governing tests, clinical programs, datasets, and statistical "
            "results did not."
        ),
    }
    chain.append(reseal)
    health["source_tree_sha256"] = rebound
    health["governance_only_reseal"] = reseal
    health["governance_reseal_chain"] = chain

    # Recheck both repository pointers immediately before the only write.  The
    # authoritative digest above is already immutable Git data; this additionally
    # prevents recording a reseal against a commit that changed during execution.
    if _resolve_commit("HEAD") != head_revision or _material_worktree_changes():
        raise SystemExit("repository changed during reseal; refusing to write pipeline health")
    atomic_write_json(HEALTH, health, ROOT, mode=0o644)
    print(f"Rebound {HEALTH.relative_to(ROOT)} from {previous} to {rebound}")
    print("Disclosure: governance-only seal update; SAS/clinical stages were not re-executed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
