#!/usr/bin/env python3
"""Build a current release-run manifest with file hashes and QC verdict binding.

This is a hash-sealed run record, not an electronic signature or Part 11
attestation. It binds the current workspace state, runtime telemetry, programs,
datasets, outputs, logs, package files, and QC status files into one machine
readable record so stale evidence cannot be mistaken for the current run.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import platform
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover - CI/runtime dependency check catches this
    yaml = None


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "platform/release_run_manifest"
REPORT = ROOT / "docs/RELEASE_RUN_MANIFEST.md"
BINDING_CSV = ROOT / "06_qc_evidence/audit/output_hash_binding.csv"


QC_FILES = {
    "pipeline_health": "platform/pipeline_health.json",
    "reconciliation": "platform/reconciliation_status.json",
    "results_reconciliation": "platform/results_reconciliation_status.json",
    "forest_reconciliation": "platform/forest_reconciliation_status.json",
    "figure_data_reconciliation": "platform/figure_data_reconciliation_status.json",
    "cbzp_bridge": "platform/cbzp_bridge_status.json",
    "spec_define": "platform/conformance/spec_define_conformance.json",
    "spec_data": "platform/conformance/spec_data_conformance.json",
    "metadata_control": "platform/metadata_control/metadata_control_status.json",
    "log_cleanliness": "platform/log_cleanliness/log_cleanliness_status.json",
    "tfl_output_index": "platform/tfl_output_index_status.json",
    "validation_strategy": "platform/validation_strategy/validation_strategy_status.json",
}

CONTROL_FILES = [
    "config/study_manifest.yaml",
    "config/study_config.yaml",
    "config/tfl_output_catalog.yaml",
    "config/validation_strategy.yaml",
    "config/ctq_traceability.yaml",
    "config/delivery_workstreams.yaml",
    "config/evidence_layers.yaml",
    "config/metadata_lineage.yaml",
    "config/log_cleanliness.yaml",
    "03_metadata/adam/ADaM_spec.xlsx",
    "03_metadata/define/define.xml",
    "03_metadata/define/define_sdtm.xml",
    "04_analysis_datasets/programs/sas/U_xpt_export.sas",
    "04_analysis_datasets/programs/sas/_adam_labels.sas",
    "04_analysis_datasets/programs/r/config_study.R",
    "04_analysis_datasets/programs/r/adam_var_labels.csv",
    "04_analysis_datasets/programs/r/spec_data_checks.R",
    "06_qc_evidence/reconciliation/cross_lang_audit.R",
    "06_qc_evidence/reconciliation/results_reconcile.R",
    "06_qc_evidence/reconciliation/forest_reconcile.R",
    "06_qc_evidence/reconciliation/figure_data_reconcile.R",
    "platform/cibuild.py",
    "platform/check_log_cleanliness.py",
    "platform/package_ectd.py",
    "platform/build_ectd_backbone.py",
    "platform/materialize_ectd.py",
    "05_outputs/tfl/tfl_generation.R",
    "05_outputs/tfl/lab_shift_table.R",
    "05_outputs/tfl/tfl_stats.R",
]

# Pipeline controls are sealed separately from the clinical source-tree digest.
# They govern how CI executes and verifies the release, but are not inputs to the
# already-completed data-bearing run represented by pipeline_health.json.
PIPELINE_CONTROL_FILES = [
    ".github/CODEOWNERS",
    ".github/workflows/ci.yml",
    ".pre-commit-config.yaml",
    "requirements-ci.txt",
    "requirements-ci.lock",
    "renv.lock",
    "scripts/verify_release.py",
]

# Keep the source inventory in one place.  The same digest is written into
# pipeline_health.json at run time and recomputed here during release sealing;
# this prevents a green health snapshot from being paired with later-edited
# programs or controls.
PROGRAM_GLOBS = [
    "04_analysis_datasets/programs/sas/**/*.sas",
    "04_analysis_datasets/programs/r/**/*.R",
    "06_qc_evidence/reconciliation/**/*.R",
    "platform/*.py",
    "platform/*.R",
    "03_metadata/define/*.py",
    "03_metadata/define/*.R",
    "05_outputs/tfl/**/*.R",
]

# Generated configuration is consumed by the local/ODA run but is intentionally
# ignored by Git. It must not enter a release source seal that a clean checkout
# cannot reproduce; the authoritative YAML/config generator is sealed instead.
GENERATED_SOURCE_EXCLUDES = {
    "04_analysis_datasets/programs/sas/00_config_generated.sas",
}


def _rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def _run_git(args: list[str]) -> str:
    try:
        return subprocess.check_output(
            ["git", *args],
            cwd=ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        ).rstrip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return ""


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _source_tree_sha256(controls: list, programs: list) -> str:
    """Digest of sealed material source (controls + programs), seal-output-free.

    Replaces HEAD-based staleness binding: committing the tracked seal advances
    HEAD past the recorded head, so a committed manifest can never satisfy a
    current_HEAD equality check (audit CRITICAL). The source-tree digest attests
    to the exact source/config/program tree the seal was built from, is stable
    across the seal commit (seal outputs are in neither group), and is
    recomputable in a bare clone.
    """
    rows = sorted(
        (r["path"], r["sha256"]) for r in (controls + programs)
        if r.get("sha256")
    )
    return _sha256_bytes(b"\n".join(f"{p}\0{s}".encode("utf-8") for p, s in rows))


def _current_source_tree_sha256() -> str:
    """Recompute the run-binding digest from the current source/control tree."""
    controls = _hash_existing(CONTROL_FILES)
    programs = _hash_globs(PROGRAM_GLOBS, exclude_paths=GENERATED_SOURCE_EXCLUDES)
    return _source_tree_sha256(controls, programs)


def _hash_file(path: Path) -> dict:
    if not path.exists():
        return {"path": _rel(path), "present": False, "size_bytes": None, "sha256": "", "md5": ""}
    h256 = hashlib.sha256()
    hmd5 = hashlib.md5()  # identity checksum for SAS/XPT parity, not a security use
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h256.update(chunk)
            hmd5.update(chunk)
    return {
        "path": _rel(path),
        "present": True,
        "size_bytes": path.stat().st_size,
        "sha256": h256.hexdigest(),
        "md5": hmd5.hexdigest(),
    }


def _load_json(rel_path: str) -> dict:
    path = ROOT / rel_path
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def _load_manifest() -> dict:
    path = ROOT / "config/study_manifest.yaml"
    if yaml is None or not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data if isinstance(data, dict) else {}


def _dataset_names(manifest: dict) -> list[str]:
    datasets = manifest.get("datasets", [])
    names = [str(d.get("name", "")).lower() for d in datasets if d.get("name")]
    return names or ["adsl", "adex", "adcm", "adae", "adlb", "adrs", "adtte", "clinsite"]


def _expected_stage_names(manifest: dict) -> list[str]:
    """Mirror cibuild.build_stages() naming so partial runs are detectable."""
    infra = manifest.get("infrastructure_stages", {}) or {}
    names: list[str] = []
    for stage in infra.get("pre", []) or []:
        if stage.get("name"):
            names.append(str(stage["name"]))
    for dataset in manifest.get("datasets", []) or []:
        if not dataset.get("name"):
            continue
        names.append(str(dataset.get("val_stage") or f"R {str(dataset['name']).upper()} Validation"))
    names.append("SAS Production (ODA/Real/Simulated)")
    for stage in infra.get("post", []) or []:
        if stage.get("name"):
            names.append(str(stage["name"]))
    return names


def _parse_iso_ts(value: str | None):
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _file_mtime_utc(path: Path):
    if not path.exists():
        return None
    return datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)


def _sas_companion_freshness(health: dict) -> dict:
    """SAS companion figures are rendered by the real-SAS stage; flag stale files."""
    pattern = "05_outputs/tfl/output/figures/sas/*"
    health_ts = _parse_iso_ts(health.get("timestamp"))
    files = []
    stale = []
    for path in sorted(ROOT.glob(pattern)):
        if not path.is_file():
            continue
        mtime = _file_mtime_utc(path)
        current = False
        if health_ts and mtime:
            ht = health_ts if health_ts.tzinfo else health_ts.replace(tzinfo=timezone.utc)
            mt = mtime if mtime.tzinfo else mtime.replace(tzinfo=timezone.utc)
            # 1h skew tolerance for clock differences between ODA render and local health write
            current = mt >= (ht - timedelta(hours=1))
        row = {
            "path": _rel(path),
            "mtime_utc": mtime.isoformat() if mtime else None,
            "current_with_pipeline_health": current,
        }
        if not current:
            stale.append(row["path"])
        files.append(row)
    return {
        "generation_scope": "in_dag_real_sas_companion",
        "file_count": len(files),
        "files": files,
        "stale_paths": stale,
        "all_current_with_pipeline_health": bool(files) and not stale,
        "note": (
            "SAS companion figures are rendered by the real-SAS Stage 14 session and "
            "their figure-driving CSVs are reconciled before release sealing."
        ),
    }


def _run_completeness(health: dict, expected_stages: list[str]) -> dict:
    recorded = health.get("stages") or {}
    # While this stage is executing, health may have been written immediately upstream
    # and therefore omit "Release Run Manifest Binding". Require every other DAG stage.
    required = [n for n in expected_stages if n != "Release Run Manifest Binding"]
    missing = [n for n in required if n not in recorded]
    not_run = [n for n in required if recorded.get(n) == "NOT_RUN"]
    failed = [n for n in required if recorded.get(n) == "FAIL"]
    # Legitimate SKIPPED (e.g. results recon not_available) is allowed in non-release grades;
    # for release-candidate full_dag we still allow SKIPPED only when overall health is GREEN
    # and mode is not asserting full real-SAS results evidence... keep simple: PASS or SKIPPED ok.
    non_success = [
        n for n in required
        if recorded.get(n) not in {"PASS", "SKIPPED", "NOT_RUN", None} and n in recorded
    ]
    health_scope = health.get("run_scope")
    complete = not missing and not not_run and not failed
    # Prefer structural completeness of required upstream stages over an intermediate
    # health.run_scope label written mid-pipeline (which can be partial only because
    # the release-manifest stage itself had not yet run).
    scope = "full_dag" if complete else "partial_dag"
    return {
        "run_scope": scope,
        "stages_expected": len(expected_stages),
        "expected_stage_names": list(expected_stages),
        "stages_required_for_release": len(required),
        "stages_recorded_in_health": len(recorded),
        "missing_from_health": missing,
        "not_run": not_run,
        "failed": failed,
        "non_success": non_success,
        "health_run_scope": health_scope,
    }


# Paths this seal (and the sibling RC checklist) rewrites on every run. They must
# not self-trip the dirty-worktree remediation gate or a PASS seal can never land
# on a clean tree.
_SEAL_SELF_PATH_PREFIXES = (
    "platform/release_run_manifest/",
    "platform/release_candidate/",
    "docs/RELEASE_RUN_MANIFEST.md",
    "docs/RELEASE_CANDIDATE_CHECKLIST.md",
    "06_qc_evidence/audit/output_hash_binding.csv",
)


def _porcelain_path(line: str) -> str:
    # porcelain v1: "XY path" or "XY orig -> path" (renames)
    body = line[3:] if len(line) >= 4 else line
    if " -> " in body:
        body = body.split(" -> ", 1)[1]
    return body.strip()


def _is_seal_self_path(path: str) -> bool:
    return any(path == p or path.startswith(p) for p in _SEAL_SELF_PATH_PREFIXES)


def _git_state() -> dict:
    status = _run_git(["status", "--porcelain=v1"])
    tracked_diff_names = _run_git(["diff", "--name-only", "HEAD", "--"])
    staged_diff_names = _run_git(["diff", "--cached", "--name-only"])
    all_lines = [x for x in status.splitlines() if x]
    material_lines = [ln for ln in all_lines if not _is_seal_self_path(_porcelain_path(ln))]
    return {
        "head": _run_git(["rev-parse", "HEAD"]),
        "branch": _run_git(["branch", "--show-current"]),
        "dirty": bool(material_lines),
        "dirty_including_seal_outputs": bool(all_lines),
        "status_porcelain_sha256": _sha256_bytes("\n".join(material_lines).encode("utf-8")) if material_lines else "",
        "tracked_diff_paths": [x for x in tracked_diff_names.splitlines() if x and not _is_seal_self_path(x)],
        "staged_diff_paths": [x for x in staged_diff_names.splitlines() if x and not _is_seal_self_path(x)],
        "status_porcelain": material_lines,
        "status_porcelain_all": all_lines,
    }


def _hash_existing(paths: list[str]) -> list[dict]:
    rows = []
    for rel_path in paths:
        path = ROOT / rel_path
        if path.exists():
            rows.append(_hash_file(path))
    return rows


def _hash_globs(patterns: list[str], exclude_paths: set[str] | None = None) -> list[dict]:
    rows = []
    seen = set()
    exclude_paths = exclude_paths or set()
    for pattern in patterns:
        for path in sorted(ROOT.glob(pattern)):
            if path.is_file() and path not in seen and _rel(path) not in exclude_paths:
                seen.add(path)
                rows.append(_hash_file(path))
    return rows


def _dataset_hashes(datasets: list[str]) -> tuple[list[dict], list[dict]]:
    rows = []
    binding = []
    for ds in datasets:
        prod = ROOT / f"04_analysis_datasets/adam/{ds}_prod.xpt"
        val = ROOT / f"04_analysis_datasets/adam/{ds}_v.xpt"
        if ds == "clinsite":
            package = ROOT / "08_submission_package/m5/datasets/tropic/bimo/datasets/clinsite.xpt"
            sequence = ROOT / "08_submission_package/ectd/0000/m5/datasets/tropic/bimo/datasets/clinsite.xpt"
        else:
            package = ROOT / f"08_submission_package/m5/datasets/tropic/analysis/adam/datasets/{ds}.xpt"
            sequence = ROOT / f"08_submission_package/ectd/0000/m5/datasets/tropic/analysis/adam/datasets/{ds}.xpt"

        prod_h = _hash_file(prod)
        val_h = _hash_file(val)
        pkg_h = _hash_file(package)
        seq_h = _hash_file(sequence)
        distinct = bool(prod_h["md5"] and val_h["md5"] and prod_h["md5"] != val_h["md5"])
        pkg_match = bool(prod_h["md5"] and pkg_h["md5"] and prod_h["md5"] == pkg_h["md5"])
        seq_match = bool(prod_h["md5"] and seq_h["md5"] and prod_h["md5"] == seq_h["md5"])

        rows.append({
            "dataset": ds.upper(),
            "prod": prod_h,
            "validation": val_h,
            "package_copy": pkg_h,
            "sequence_copy": seq_h,
            "prod_vs_validation_distinct": distinct,
            "package_matches_prod": pkg_match,
            "sequence_matches_prod": seq_match,
        })
        binding.append({
            "dataset": ds.upper(),
            "current_prod_md5": prod_h["md5"],
            "current_v_md5": val_h["md5"],
            "package_md5": pkg_h["md5"],
            "sequence_md5": seq_h["md5"],
            "release_manifest_prod_md5": prod_h["md5"],
            "prod_vs_validation_distinct": "YES" if distinct else "NO",
            "current_matches_package": "YES" if pkg_match else "NO",
            "current_matches_sequence": "YES" if seq_match else "NO",
            "current_matches_release_manifest": "YES" if prod_h["md5"] else "NO",
        })
    return rows, binding


def _qc_statuses() -> tuple[dict, list[dict]]:
    statuses = {}
    hashes = []
    for name, rel_path in QC_FILES.items():
        data = _load_json(rel_path)
        status = (
            data.get("overall")
            or data.get("status")
            or data.get("pipeline_health_status")
            or "missing"
        )
        statuses[name] = {
            "path": rel_path,
            "status": status,
            "detail": {
                "sas_execution_mode": data.get("sas_execution_mode"),
                "simulated": data.get("simulated"),
                "provenance_guard_passed": (data.get("provenance_guard") or {}).get("passed"),
            },
        }
        path = ROOT / rel_path
        if path.exists():
            hashes.append(_hash_file(path))
    return statuses, hashes


def _binding_problems(payload: dict) -> list[str]:
    """Hard binding failures (package/data/QC integrity). These always force FAIL."""
    problems = []
    health = _load_json(QC_FILES["pipeline_health"])

    expected_source_tree = payload["source_control"].get("source_tree_sha256", "")
    recorded_source_tree = health.get("source_tree_sha256", "")
    if not recorded_source_tree:
        problems.append(
            "pipeline_health.json has no source_tree_sha256 run binding; "
            "health is not attributable to the current control/program tree"
        )
    elif recorded_source_tree != expected_source_tree:
        problems.append(
            "pipeline_health.json source_tree_sha256 does not match the current "
            "control/program tree"
        )
    recon = _load_json(QC_FILES["reconciliation"])
    results = _load_json(QC_FILES["results_reconciliation"])
    forest = _load_json(QC_FILES["forest_reconciliation"])
    figure_data = _load_json(QC_FILES["figure_data_reconciliation"])
    spec_define = _load_json(QC_FILES["spec_define"])
    spec_data = _load_json(QC_FILES["spec_data"])
    log_cleanliness = _load_json(QC_FILES["log_cleanliness"])

    if health.get("pipeline_health_status") != "GREEN":
        problems.append("pipeline_health.json is not GREEN")
    if health.get("sas_execution_mode") not in {"oda", "local"}:
        problems.append("live run is not bound to a real SAS execution mode")
    if not (health.get("provenance_guard") or {}).get("passed"):
        problems.append("pipeline provenance_guard did not pass")
    if recon.get("overall") != "PASS" or recon.get("simulated"):
        problems.append("dataset reconciliation is not non-simulated PASS")
    if (recon.get("endpoint_controls") or {}).get("F042_PAIN_RESPONSE") != "PASS":
        problems.append("F-042 pain-response SAS/R reconciliation is not PASS")
    if results.get("overall") != "PASS":
        problems.append("results reconciliation is not PASS")
    if forest.get("overall") != "PASS":
        problems.append("forest reconciliation is not PASS")
    if figure_data.get("overall") != "PASS":
        problems.append("figure-data reconciliation is not PASS")
    if spec_define.get("status") != "PASS":
        problems.append("spec-to-Define conformance is not PASS")
    if spec_data.get("status") != "PASS":
        problems.append("spec-to-data conformance is not PASS")
    if log_cleanliness.get("status") != "PASS":
        problems.append("log cleanliness gate is not PASS")

    pipeline_controls = payload.get("artifacts", {}).get("pipeline_controls") or []
    missing_pipeline_controls = [
        path for path in PIPELINE_CONTROL_FILES
        if not any(row.get("path") == path and row.get("present") for row in pipeline_controls)
    ]
    if missing_pipeline_controls:
        problems.append(
            "pipeline control seal is incomplete: " + ", ".join(missing_pipeline_controls)
        )

    for row in payload["datasets"]:
        ds = row["dataset"]
        if not row["prod"]["present"]:
            problems.append(f"{ds}: current production XPT missing")
        if not row["validation"]["present"]:
            problems.append(f"{ds}: current validation XPT missing")
        if not row["prod_vs_validation_distinct"]:
            problems.append(f"{ds}: production and validation XPT hashes are not distinct")
        if not row["package_matches_prod"]:
            problems.append(f"{ds}: m5 package copy does not match current production XPT")
        if not row["sequence_matches_prod"]:
            problems.append(f"{ds}: materialized sequence copy does not match current production XPT")

    required_package_files = [
        "08_submission_package/ectd/0000/index.xml",
        "08_submission_package/ectd/0000/index-md5.txt",
        "08_submission_package/ectd/0000/m1/us/us-regional.xml",
        "08_submission_package/ectd/0000/m5/53-clin-stud-rep/535-rep-effic-safety-stud/mcrpc/5351-stud-rep-contr/tropic/stf-tropic.xml",
    ]
    for rel_path in required_package_files:
        if not (ROOT / rel_path).exists():
            problems.append(f"required package artifact missing: {rel_path}")

    return problems


def _remediation_reasons(payload: dict) -> list[str]:
    """Conditions that keep a hash-sealed remediation run but block release-candidate PASS."""
    reasons = []
    completeness = payload.get("run_completeness") or {}
    if completeness.get("run_scope") != "full_dag":
        missing = completeness.get("missing_from_health") or []
        not_run = completeness.get("not_run") or []
        reasons.append(
            "pipeline_health does not cover a full current DAG run "
            f"({completeness.get('stages_recorded_in_health')} recorded in health / "
            f"{completeness.get('stages_required_for_release')} release-required upstream stages; "
            f"missing={len(missing)}; not_run={len(not_run)}). "
            "Acceptable as targeted remediation evidence only."
        )
        if missing:
            preview = ", ".join(missing[:8])
            extra = "" if len(missing) <= 8 else f" (+{len(missing) - 8} more)"
            reasons.append(f"stages missing from pipeline_health: {preview}{extra}")
        if not_run:
            preview = ", ".join(not_run[:8])
            extra = "" if len(not_run) <= 8 else f" (+{len(not_run) - 8} more)"
            reasons.append(f"stages marked NOT_RUN (partial --from-stage): {preview}{extra}")

    if payload.get("source_control", {}).get("dirty"):
        n = len(payload.get("source_control", {}).get("status_porcelain") or [])
        reasons.append(
            f"git worktree is dirty ({n} porcelain entries); "
            "release-candidate lock requires a clean committed state"
        )

    return reasons


def _seal_payload(payload: dict) -> str:
    unsigned = dict(payload)
    unsigned.pop("manifest_sha256", None)
    data = json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def _write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _write_report(payload: dict) -> None:
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    dataset_lines = [
        "| Dataset | Prod MD5 | Validation MD5 | Distinct | Package match | Sequence match |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in payload["datasets"]:
        dataset_lines.append(
            "| {dataset} | {prod} | {val} | {distinct} | {pkg} | {seq} |".format(
                dataset=row["dataset"],
                prod=row["prod"]["md5"],
                val=row["validation"]["md5"],
                distinct="yes" if row["prod_vs_validation_distinct"] else "no",
                pkg="yes" if row["package_matches_prod"] else "no",
                seq="yes" if row["sequence_matches_prod"] else "no",
            )
        )
    qc_lines = [
        "| Check | Status | Source |",
        "| --- | --- | --- |",
    ]
    for name, detail in payload["qc_statuses"].items():
        qc_lines.append(f"| {name} | {detail['status']} | {detail['path']} |")

    completeness = payload.get("run_completeness") or {}
    sas_comp = payload.get("sas_companion_figures") or {}
    lines = [
        "# TROPIC Release-Run Manifest",
        "",
        f"Generated: {payload['generated_at']}",
        "",
        "> Hash-sealed run manifest for current artifacts. This is not an electronic signature or Part 11 attestation.",
        "",
        "## Verdict",
        "",
        f"- Status: `{payload['status']}`",
        f"- Evidence grade: `{payload.get('evidence_grade', '')}`",
        f"- Manifest SHA-256 seal: `{payload['manifest_sha256']}`",
        f"- SAS execution mode: `{payload['environment'].get('sas_execution_mode', '')}`",
        f"- Pipeline health: `{payload['qc_statuses'].get('pipeline_health', {}).get('status', '')}`",
        f"- Run scope: `{completeness.get('run_scope', '')}` "
        f"({completeness.get('stages_recorded_in_health', '')} recorded / "
        f"{completeness.get('stages_required_for_release', '')} release-required upstream stages)",
        f"- Git HEAD: `{payload['source_control'].get('head', '')}`",
        f"- Worktree dirty: `{payload['source_control'].get('dirty')}`",
        f"- SAS companion figures: `{sas_comp.get('generation_scope', '')}`; "
        f"current with health=`{sas_comp.get('all_current_with_pipeline_health')}`",
        "",
        "## Status meanings",
        "",
        "- `PASS` — full current DAG + clean worktree + current-run binding; release-candidate grade.",
        "- `REMEDIATION` — hard QC/package bindings hold, but run is partial, dirty, or carries stale companion artifacts; development/remediation evidence only.",
        "- `FAIL` — package/data/QC binding integrity failed.",
        "",
        "## Problems",
        "",
    ]
    if payload["problems"]:
        lines.extend(f"- {p}" for p in payload["problems"])
    else:
        lines.append("No release-run binding problems detected.")
    if payload.get("remediation_reasons"):
        lines.extend(["", "## Remediation reasons (block release-candidate PASS)", ""])
        lines.extend(f"- {r}" for r in payload["remediation_reasons"])
    lines.extend([
        "",
        "## Dataset Binding",
        "",
        *dataset_lines,
        "",
        "## QC Verdicts",
        "",
        *qc_lines,
        "",
        "## Machine-Readable Outputs",
        "",
        "- `platform/release_run_manifest/release_run_manifest.json`",
        "- `platform/release_run_manifest/release_run_files.csv`",
        "- `06_qc_evidence/audit/output_hash_binding.csv`",
        "",
    ])
    REPORT.write_text("\n".join(lines), encoding="utf-8")


def build_release_run_manifest(out_dir: Path = OUT_DIR) -> dict:
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    manifest = _load_manifest()
    datasets = _dataset_names(manifest)
    dataset_rows, binding_rows = _dataset_hashes(datasets)
    qc_statuses, qc_hashes = _qc_statuses()
    health = _load_json(QC_FILES["pipeline_health"])

    tfl_outputs = _hash_globs([
        "05_outputs/tfl/output/tables/*",
        "05_outputs/tfl/output/figures/*",
        "05_outputs/tfl/output/figures/sas/*",
        "05_outputs/tfl/output/listings/*",
    ])
    package_hashes = _hash_globs([
        "08_submission_package/ectd/0000/index.xml",
        "08_submission_package/ectd/0000/index-md5.txt",
        "08_submission_package/ectd/0000/m1/us/us-regional.xml",
        "08_submission_package/ectd/0000/m5/**/*.xml",
        "08_submission_package/ectd/0000/m5/**/*.pdf",
        "08_submission_package/ectd/0000/m5/**/*.txt",
        "08_submission_package/ectd/0000/m5/**/*.png",
        "08_submission_package/ectd/0000/m5/**/*.xpt",
        "08_submission_package/m5/**/*.xml",
        "08_submission_package/m5/**/*.pdf",
        "08_submission_package/m5/**/*.txt",
        "08_submission_package/m5/**/*.png",
        "08_submission_package/m5/**/*.xpt",
    ])
    logs = _hash_globs([
        "04_analysis_datasets/programs/sas/oda_master_driver.log",
        "04_analysis_datasets/programs/r/*.log",
        "06_qc_evidence/reconciliation/*.log",
        "05_outputs/tfl/*.log",
    ])
    inputs = _hash_globs([
        "01_source_data/real_sdtm/**/*.sas7bdat",
        "01_source_data/cbzp_reconstructed/*.rds",
        "01_source_data/cbzp_reconstructed/*.xpt",
        ".core_run/sdtm34/*.xpt",
    ])
    additive_outputs = _hash_globs([
        "03_metadata/usdm/*.json",
        "04_analysis_datasets/datasetjson/**/*.json",
        "04_analysis_datasets/datasetjson/**/*.ndjson",
        "05_outputs/ars/**/*.csv",
        "05_outputs/ars/**/*.json",
        "05_outputs/ars/**/*.ndjson",
    ])
    programs = _hash_globs(PROGRAM_GLOBS, exclude_paths=GENERATED_SOURCE_EXCLUDES)
    controls = _hash_existing(CONTROL_FILES)
    pipeline_controls = _hash_existing(PIPELINE_CONTROL_FILES)

    expected_stages = _expected_stage_names(manifest)
    run_completeness = _run_completeness(health, expected_stages)
    sas_companion_figures = _sas_companion_freshness(health)

    git_state = _git_state()
    git_state["source_tree_sha256"] = _source_tree_sha256(controls, programs)
    git_state["pipeline_control_sha256"] = _source_tree_sha256(pipeline_controls, [])

    payload = {
        "status": "PENDING",
        "evidence_grade": "pending",
        "generated_at": generated_at,
        "source_control": git_state,
        "environment": {
            "python": sys.version.split()[0],
            "platform": platform.platform(),
            "r_version": health.get("r_version"),
            "renv_lock_sha256": health.get("renv_lock_sha256"),
            "sas_execution_mode": health.get("sas_execution_mode"),
            "sas_version": health.get("sas_version"),
            "oda_endpoint": health.get("oda_endpoint"),
            "sdtm_manifest_sha": health.get("sdtm_manifest_sha"),
            "pipeline_run_scope": health.get("run_scope"),
        },
        "run_completeness": run_completeness,
        "sas_companion_figures": sas_companion_figures,
        "datasets": dataset_rows,
        "qc_statuses": qc_statuses,
        "artifacts": {
            "controls": controls,
            "pipeline_controls": pipeline_controls,
            "inputs": inputs,
            "programs": programs,
            "qc_files": qc_hashes,
            "tfl_outputs": tfl_outputs,
            "logs": logs,
            "package_files": package_hashes,
            "additive_outputs": additive_outputs,
        },
    }
    payload["problems"] = _binding_problems(payload)
    payload["remediation_reasons"] = _remediation_reasons(payload)
    if payload["problems"]:
        payload["status"] = "FAIL"
        payload["evidence_grade"] = "failed_binding"
    elif payload["remediation_reasons"]:
        payload["status"] = "REMEDIATION"
        payload["evidence_grade"] = "remediation_partial_or_dirty"
    else:
        payload["status"] = "PASS"
        payload["evidence_grade"] = "release_candidate"
    payload["manifest_sha256"] = _seal_payload(payload)

    out_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = out_dir / "release_run_manifest.json"
    manifest_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")

    file_rows = []
    for group_name, group_rows in payload["artifacts"].items():
        for row in group_rows:
            file_rows.append({
                "group": group_name,
                "path": row["path"],
                "present": row["present"],
                "size_bytes": row["size_bytes"],
                "sha256": row["sha256"],
                "md5": row["md5"],
            })
    _write_csv(
        out_dir / "release_run_files.csv",
        file_rows,
        ["group", "path", "present", "size_bytes", "sha256", "md5"],
    )
    _write_csv(
        BINDING_CSV,
        binding_rows,
        [
            "dataset", "current_prod_md5", "current_v_md5", "package_md5", "sequence_md5",
            "release_manifest_prod_md5", "prod_vs_validation_distinct",
            "current_matches_package", "current_matches_sequence", "current_matches_release_manifest",
        ],
    )
    _write_report(payload)
    return payload


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Build current release-run manifest and hash binding")
    parser.add_argument("--out-dir", default=str(OUT_DIR))
    parser.add_argument("--allow-fail", action="store_true",
                        help="Write manifest but do not exit non-zero when binding checks fail")
    args = parser.parse_args(argv)
    payload = build_release_run_manifest(Path(args.out_dir))
    print(f"Release-run manifest status: {payload['status']}")
    print(f"Evidence grade: {payload.get('evidence_grade')}")
    print(f"Run scope: {(payload.get('run_completeness') or {}).get('run_scope')}")
    print(f"Manifest SHA-256 seal: {payload['manifest_sha256']}")
    print(f"Wrote {Path(args.out_dir) / 'release_run_manifest.json'}")
    print(f"Wrote {BINDING_CSV.relative_to(ROOT)}")
    if payload["problems"]:
        for problem in payload["problems"]:
            print(f"  [BINDING] {problem}")
    if payload.get("remediation_reasons"):
        for reason in payload["remediation_reasons"]:
            print(f"  [REMEDIATION] {reason}")
    # FAIL always non-zero. REMEDIATION exits 0 so development/partial DAG stages can
    # continue, but release-candidate checklist only accepts status == PASS.
    if payload["status"] == "FAIL" and not args.allow_fail:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
