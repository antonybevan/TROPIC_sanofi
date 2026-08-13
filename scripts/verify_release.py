#!/usr/bin/env python3
"""Path A release verification without re-running ODA/SAS.

Rechecks sealed control JSONs, product claim docs, and findings disposition.
Exit 0 only if all hard checks pass.
"""
from __future__ import annotations

import csv
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SEAL_SELF_PATH_PREFIXES = (
    "platform/release_run_manifest/",
    "platform/release_candidate/",
    "docs/RELEASE_RUN_MANIFEST.md",
    "docs/RELEASE_CANDIDATE_CHECKLIST.md",
    "06_qc_evidence/audit/output_hash_binding.csv",
)

ARTIFACT_GROUPS = (
    "qc_files",
    "tfl_outputs",
    "package_files",
    "additive_outputs",
    "inputs",
    "logs",
    "review_surface",
)


def load(rel: str):
    path = ROOT / rel
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def git_head() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, stderr=subprocess.DEVNULL
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return ""


def porcelain_path(line: str) -> str:
    body = line[3:] if len(line) >= 4 else line
    if " -> " in body:
        body = body.split(" -> ", 1)[1]
    return body.strip()


def is_seal_self_path(path: str) -> bool:
    return any(path == prefix or path.startswith(prefix) for prefix in SEAL_SELF_PATH_PREFIXES)


def git_material_worktree_clean() -> bool:
    """Match the release-manifest dirty gate: ignore files rewritten by sealing itself."""
    try:
        status = subprocess.check_output(
            ["git", "status", "--porcelain=v1"], cwd=ROOT, text=True, stderr=subprocess.DEVNULL
        )
        material_lines = [
            line for line in status.splitlines()
            if line and not is_seal_self_path(porcelain_path(line))
        ]
        return not material_lines
    except (OSError, subprocess.CalledProcessError):
        return False


def manifest_sha256(manifest: dict) -> str:
    """Recompute the canonical release-manifest self-seal."""
    unsigned = dict(manifest)
    unsigned.pop("manifest_sha256", None)
    encoded = json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def sealed_source_problems(manifest: dict) -> list[str]:
    """Return changed/missing source files recorded by the release seal.

    Controls, programs, and pipeline controls are checked. Data-bearing and runtime
    artifact groups are checked separately because a data-free CI checkout may not
    contain ignored XPTs/logs.
    """
    problems = []
    artifacts = manifest.get("artifacts") or {}
    for group in ("controls", "programs", "pipeline_controls"):
        if group == "pipeline_controls" and group not in artifacts:
            continue
        for row in artifacts.get(group) or []:
            rel = row.get("path")
            expected = row.get("sha256")
            if not rel or not expected:
                problems.append(f"{group}: invalid seal entry {row!r}")
                continue
            path = ROOT / rel
            if not path.is_file():
                problems.append(f"{rel}: missing")
            elif sha256(path) != expected:
                problems.append(rel)
    return problems


def _git_tracked(rel: str) -> bool:
    """Return whether a missing path is versioned in the current checkout."""
    try:
        subprocess.check_output(
            ["git", "ls-files", "--error-unmatch", "--", rel],
            cwd=ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        )
        return True
    except (OSError, subprocess.CalledProcessError):
        return False


def _safe_path(rel: str) -> Path | None:
    """Resolve a manifest path without allowing it to escape the repository root."""
    candidate = (ROOT / rel).resolve()
    root = ROOT.resolve()
    if candidate != root and root not in candidate.parents:
        return None
    return candidate


def sealed_artifact_problems(manifest: dict) -> tuple[list[str], int, int]:
    """Rehash sealed runtime artifacts that are present in this checkout.

    A clean CI checkout intentionally omits ignored patient-level XPTs and some
    package payloads. Missing untracked rows are therefore reported as skipped,
    while every present row is always rehashed and every missing tracked row fails.
    This catches post-seal edits to both tracked and ignored artifacts.
    """
    artifacts = manifest.get("artifacts") or {}
    problems: list[str] = []
    verified = 0
    skipped = 0
    for group in ARTIFACT_GROUPS:
        if group not in artifacts:
            problems.append(f"{group}: artifact group missing from release seal")
            continue
        for row in artifacts.get(group) or []:
            rel = row.get("path")
            expected = row.get("sha256")
            if not rel or not expected:
                # Dataset rows can legitimately carry present=false/sha256="";
                # runtime artifact rows cannot.
                if row.get("present") is not False:
                    problems.append(f"{group}: invalid seal entry {row!r}")
                continue
            path = _safe_path(rel)
            if path is None:
                problems.append(f"{group}:{rel}: path escapes repository root")
                continue
            if not path.is_file():
                if _git_tracked(rel):
                    problems.append(f"{group}:{rel}: tracked artifact missing")
                else:
                    skipped += 1
                continue
            actual = sha256(path)
            if actual != expected:
                problems.append(f"{group}:{rel}: sha256 mismatch")
            else:
                verified += 1

    for dataset in manifest.get("datasets") or []:
        ds = dataset.get("dataset", "?")
        for label in ("prod", "validation", "package_copy", "sequence_copy"):
            row = dataset.get(label) or {}
            rel = row.get("path")
            expected = row.get("sha256")
            if not rel or not expected:
                continue
            path = _safe_path(rel)
            if path is None:
                problems.append(f"datasets:{ds}:{label}: path escapes repository root")
            elif not path.is_file():
                if _git_tracked(rel):
                    problems.append(f"datasets:{ds}:{label}: tracked artifact missing")
                else:
                    skipped += 1
            elif sha256(path) != expected:
                problems.append(f"datasets:{ds}:{label}: sha256 mismatch")
            else:
                verified += 1
    return problems, verified, skipped


def rows_sha256(rows: list[dict]) -> str:
    """Digest a sealed path/hash row list in the same canonical form as the builder."""
    encoded = "\n".join(
        f"{row.get('path')}\0{row.get('sha256')}"
        for row in sorted(rows, key=lambda item: (item.get("path", ""), item.get("sha256", "")))
        if row.get("sha256")
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def source_tree_sha256(manifest: dict) -> str:
    """Recompute the seal's source-tree digest from files currently on disk.

    Only rows whose on-disk bytes still match the recorded hash enter the digest,
    so a single changed source file both fails sealed_source_problems() and
    changes this digest. Seal outputs are not in controls/programs, so the digest
    is stable across the seal's own commit (audit CRITICAL: a tracked seal can
    never satisfy a recorded-head == current-HEAD equality check).
    """
    rows = []
    artifacts = manifest.get("artifacts") or {}
    for group in ("controls", "programs"):
        for row in artifacts.get(group) or []:
            rel = row.get("path")
            expected = row.get("sha256")
            if not rel or not expected:
                continue
            path = ROOT / rel
            if path.is_file() and sha256(path) == expected:
                rows.append((rel, expected))
    h = hashlib.sha256()
    h.update(b"\n".join(f"{rel}\0{expected}".encode("utf-8") for rel, expected in sorted(rows)))
    return h.hexdigest()


def main() -> int:
    checks: list[tuple[str, bool, str]] = []

    def add(name: str, cond: bool, detail: str = "") -> None:
        checks.append((name, bool(cond), detail))

    h = load("platform/pipeline_health.json") or {}
    stages = h.get("stages") or {}
    add("health.schema_version", h.get("schema_version") == "run_scope_v1", str(h.get("schema_version")))
    add("health.status_GREEN", h.get("pipeline_health_status") == "GREEN", str(h.get("pipeline_health_status")))
    add("health.mode_real_sas", h.get("sas_execution_mode") in {"oda", "local"}, str(h.get("sas_execution_mode")))
    add("health.full_dag", h.get("run_scope") == "full_dag", str(h.get("run_scope")))
    add(
        "health.full_stage_count",
        # The exact stage-set check below is bound to the release manifest. Keep this
        # count check as a readable health-snapshot sanity check as well.
        int(h.get("stages_expected") or 0) >= 30 and len(stages) >= 30
        and int(h.get("stages_expected") or 0) == len(stages),
        f"expected={h.get('stages_expected')} n={len(stages)}",
    )
    add("health.no_not_run", not (h.get("stages_not_run") or []), str(h.get("stages_not_run")))
    non_pass = [k for k, v in stages.items() if v not in {"PASS", "SKIPPED"}]
    add("health.all_pass_or_skip", not non_pass, str(non_pass[:8]))
    add("health.provenance", (h.get("provenance_guard") or {}).get("passed") is True, "")
    governance_reseal = h.get("governance_only_reseal") or {}
    if governance_reseal:
        add(
            "health.governance_only_reseal",
            governance_reseal.get("status") == "PASS"
            and governance_reseal.get("clinical_run_was_not_reexecuted") is True
            and governance_reseal.get("rebound_source_tree_sha256") == h.get("source_tree_sha256"),
            "governance-only rebind disclosure is incomplete",
        )

    r = load("platform/reconciliation_status.json") or {}
    add("recon.PASS", r.get("overall") == "PASS", str(r.get("overall")))
    add("recon.not_sim", r.get("simulated") is False, str(r.get("simulated")))
    f042_recon = (r.get("endpoint_controls") or {}).get("F042_PAIN_RESPONSE")
    add("recon.F042_PAIN_RESPONSE", f042_recon == "PASS", str(f042_recon))

    rr = load("platform/results_reconciliation_status.json") or {}
    add("results_recon.PASS", rr.get("overall") == "PASS", str(rr.get("overall")))

    adm = load("platform/admiral_reconciliation_status.json") or {}
    add("admiral.PASS", adm.get("overall") == "PASS", str(adm.get("overall")))
    add(
        "admiral.dag_stage",
        stages.get("Admiral Core Reconciliation") == "PASS",
        str(stages.get("Admiral Core Reconciliation")),
    )

    tfl = load("platform/tfl_output_index_status.json") or {}
    add("tfl.pass", tfl.get("status") == "pass", str(tfl.get("status")))
    cc = tfl.get("controlled_catalog") or {}
    add("tfl.catalog_pass", cc.get("status", "pass") == "pass", str(cc.get("status")))

    vs = load("platform/validation_strategy/validation_strategy_status.json") or {}
    add("validation_strategy.PASS", vs.get("status") == "PASS", str(vs.get("status")))

    lg = load("platform/log_cleanliness/log_cleanliness_status.json") or {}
    add("log_cleanliness.PASS", lg.get("status") == "PASS", str(lg.get("status")))

    rb = load("06_qc_evidence/gates/regulatory_baseline_status.json") or {}
    add("regulatory_baseline.PASS", rb.get("status") == "PASS", str(rb.get("status")))

    rm = load("platform/release_run_manifest/release_run_manifest.json") or {}
    expected_manifest_sha = rm.get("manifest_sha256", "")
    actual_manifest_sha = manifest_sha256(rm) if rm else ""
    add("release_manifest.seal", bool(expected_manifest_sha) and expected_manifest_sha == actual_manifest_sha,
        "manifest SHA-256 does not match payload" if expected_manifest_sha != actual_manifest_sha else "")
    sealed_tree = (rm.get("source_control") or {}).get("source_tree_sha256")
    actual_tree = source_tree_sha256(rm) if rm else ""
    add("release_manifest.source_tree_matches", bool(sealed_tree) and sealed_tree == actual_tree,
        "sealed source-tree digest does not match the current checkout"
        if sealed_tree != actual_tree else "")
    recorded_clean = (rm.get("source_control") or {}).get("dirty") is False
    add("release_manifest.recorded_clean_worktree", recorded_clean,
        str((rm.get("source_control") or {}).get("dirty")))
    add("release_manifest.current_material_worktree_clean", git_material_worktree_clean(),
        "git worktree has material dirt outside release seal outputs")
    source_problems = sealed_source_problems(rm) if rm else ["release manifest missing"]
    add("release_manifest.source_hashes", not source_problems,
        ", ".join(source_problems[:8]) + (" ..." if len(source_problems) > 8 else ""))
    expected_stage_names = (rm.get("run_completeness") or {}).get("expected_stage_names") or []
    actual_stage_names = list(stages)
    add(
        "release_manifest.stage_set_matches",
        bool(expected_stage_names)
        and len(actual_stage_names) == len(expected_stage_names)
        and set(actual_stage_names) == set(expected_stage_names),
        f"health={len(actual_stage_names)} manifest={len(expected_stage_names)}",
    )
    artifact_problems, verified_artifacts, skipped_artifacts = (
        sealed_artifact_problems(rm) if rm else (["release manifest missing"], 0, 0)
    )
    add(
        "release_manifest.artifact_hashes",
        not artifact_problems,
        "; ".join(artifact_problems[:8])
        + (" ..." if len(artifact_problems) > 8 else "")
        + f" (verified={verified_artifacts}, optional_missing={skipped_artifacts})",
    )
    pipeline_rows = (rm.get("artifacts") or {}).get("pipeline_controls") if rm else None
    expected_pipeline_digest = (rm.get("source_control") or {}).get("pipeline_control_sha256")
    pipeline_digest = rows_sha256(pipeline_rows or [])
    add(
        "release_manifest.pipeline_controls",
        bool(pipeline_rows)
        and not any(p.startswith("pipeline_controls:") for p in source_problems)
        and bool(expected_pipeline_digest)
        and pipeline_digest == expected_pipeline_digest,
        "pipeline CI/control files are not bound to the release seal",
    )
    add("release_manifest.PASS", rm.get("status") == "PASS", str(rm.get("status")))
    add(
        "release_manifest.grade",
        rm.get("evidence_grade") == "release_candidate",
        str(rm.get("evidence_grade")),
    )

    rc = load("platform/release_candidate/release_candidate_status.json") or {}
    add("release_candidate.PASS", rc.get("status") == "PASS", str(rc.get("status")))
    add("release_candidate.blockers_0", rc.get("blocker", 1) == 0, str(rc.get("blocker")))

    try:
        sys.path.insert(0, str(ROOT / "platform"))
        from validate_ectd_sequence import validate_sequence

        # The lightweight Path-A seal job intentionally installs no Python
        # dependencies. Full DTD validation runs in G08/validate CI; this check
        # still rejects extras, missing support files, broken references, and
        # checksum drift in every leaf that is present in a data-free checkout.
        ectd = validate_sequence(require_all_leaves=False, validate_dtd=False)
        ectd_ok = ectd.get("status") == "PASS"
        ectd_detail = (
            f"present_leaves={ectd.get('present_leaves', 0)}/"
            f"{ectd.get('checksum_leaves', 0)}; "
            + "; ".join(ectd.get("problems", [])[:5])
        )
    except Exception as exc:
        ectd_ok = False
        ectd_detail = f"validator exception: {exc}"
    add("ectd.sequence_surface", ectd_ok, ectd_detail)

    add("product_claim.exists", (ROOT / "docs/PRODUCT_CLAIM.md").is_file(), "")
    add(
        "known_diff_memo.exists",
        (ROOT / "docs/workstreams/WS5_KNOWN_DIFFERENCES_MEMO.md").is_file(),
        "",
    )
    add(
        "workstream_board.exists",
        (ROOT / "docs/WORKSTREAM_EXECUTION_BOARD.md").is_file(),
        "",
    )

    findings_path = ROOT / "06_qc_evidence/audit/findings_register.csv"
    if findings_path.is_file():
        rows = list(csv.DictReader(findings_path.open(encoding="utf-8")))
        active_conf = [
            r["ID"]
            for r in rows
            if str(r.get("status", "")).upper() == "CONFIRMED"
            and str(r.get("severity", "")).title() in {"Critical", "Major"}
        ]
        add("findings.no_confirmed_crit_major", not active_conf, str(active_conf))
    else:
        add("findings.no_confirmed_crit_major", False, "missing findings_register.csv")

    print("=== TROPIC Path A release verification (no ODA rerun) ===")
    print(f"root: {ROOT}")
    print()
    for name, cond, detail in checks:
        if cond:
            print(f"OK:   {name}")
        else:
            print(f"FAIL: {name}" + (f" ({detail})" if detail else ""))
    passed = sum(1 for _, c, _ in checks if c)
    print("---")
    print(f"summary: {passed}/{len(checks)} checks passed")
    if passed != len(checks):
        print("VERIFY_RELEASE: FAIL")
        return 1
    print("VERIFY_RELEASE: PASS")
    print("Note: Rechecks seals/control JSONs only; does not prove SAS is still reachable.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
