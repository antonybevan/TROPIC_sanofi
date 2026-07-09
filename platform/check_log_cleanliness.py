#!/usr/bin/env python3
"""Scan SAS/R execution logs for unapproved issues.

The intent is not to demand a cosmetically empty log. A reviewed, scientifically
justified exception can remain visible, but it must be explicit, capped, and
reported. Anything else in the configured issue classes fails the gate.
"""

from __future__ import annotations

import argparse
import csv
import fnmatch
import glob
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover - CI dependency installation covers this
    yaml = None


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = ROOT / "config/log_cleanliness.yaml"
OUT_DIR = ROOT / "platform/log_cleanliness"
REPORT = ROOT / "docs/LOG_CLEANLINESS_REPORT.md"


def _load_yaml(path: Path) -> dict:
    if yaml is None:
        raise RuntimeError("PyYAML is required to read log cleanliness rules")
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        raise RuntimeError(f"{path} did not parse to a YAML mapping")
    return data


def _rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def _expand(spec: str) -> list[Path]:
    if any(ch in spec for ch in "*?["):
        return sorted(Path(p) for p in glob.glob(str(ROOT / spec), recursive=True) if Path(p).is_file())
    path = ROOT / spec
    return [path] if path.is_file() else []


def _compile_rules(rows: list[dict]) -> list[dict]:
    compiled = []
    for row in rows:
        item = dict(row)
        item["_regex"] = re.compile(str(row["regex"]), re.IGNORECASE)
        compiled.append(item)
    return compiled


def _file_applies(rel_path: str, patterns: list[str]) -> bool:
    return any(fnmatch.fnmatch(rel_path, pattern) for pattern in patterns)


def _find_rule(line: str, rules: list[dict]) -> dict | None:
    stripped = line.strip()
    for rule in rules:
        if rule["_regex"].search(stripped):
            return rule
    return None


def _find_exception(rel_path: str, line: str, exceptions: list[dict]) -> dict | None:
    stripped = line.strip()
    for exception in exceptions:
        if not _file_applies(rel_path, exception.get("files", [])):
            continue
        if exception["_regex"].search(stripped):
            return exception
    return None


def _finding(status: str, rel_path: str, line_no: int | str, rule: dict, line: str) -> dict:
    return {
        "status": status,
        "file": rel_path,
        "line": line_no,
        "rule_id": rule.get("id", ""),
        "severity": rule.get("severity", ""),
        "message": line.strip(),
        "rationale": rule.get("rationale", ""),
        "owner": rule.get("owner", ""),
    }


def _scan_log(path: Path, fail_rules: list[dict], exceptions: list[dict]) -> list[dict]:
    rel_path = _rel(path)
    findings = []
    with path.open("r", encoding="utf-8", errors="replace") as f:
        for line_no, line in enumerate(f, start=1):
            rule = _find_rule(line, fail_rules)
            if rule is None:
                continue
            exception = _find_exception(rel_path, line, exceptions)
            if exception is not None:
                findings.append(_finding("REVIEWED_EXCEPTION", rel_path, line_no, exception, line))
            else:
                findings.append(_finding("UNAPPROVED", rel_path, line_no, rule, line))
    return findings


def _md_table(headers: list[str], rows: list[list[object]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for row in rows:
        clean = [str(v).replace("|", "\\|").replace("\n", " ") for v in row]
        lines.append("| " + " | ".join(clean) + " |")
    return "\n".join(lines)


def _write_outputs(status: dict, findings: list[dict], report_path: Path, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)

    status_path = out_dir / "log_cleanliness_status.json"
    findings_path = out_dir / "log_findings.csv"
    status_path.write_text(json.dumps({**status, "items": findings}, indent=2), encoding="utf-8")

    fields = ["status", "file", "line", "rule_id", "severity", "message", "rationale", "owner"]
    with findings_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(findings)

    exception_rows = [
        [row["id"], row["count"], row["max_count"], row["status"], row["rationale"]]
        for row in status["reviewed_exception_caps"]
    ]
    excluded_rows = [
        [row.get("path", ""), row.get("rationale", "")]
        for row in status.get("excluded_logs", [])
    ]
    unapproved = [f for f in findings if f["status"] == "UNAPPROVED"]
    missing = [f for f in findings if f["status"] == "MISSING_LOG"]

    lines = [
        "# TROPIC Log Cleanliness Report",
        "",
        f"Generated: {status['generated_at']}",
        "",
        "> Automated scan of **configured persisted** SAS/R execution logs. "
        "Reviewed exceptions remain visible and capped; unapproved issues fail the gate. "
        "This gate does **not** scan ephemeral rscript/python stage stdout/stderr "
        "(those streams are not persisted by `cibuild.py`).",
        "",
        "## Verdict",
        "",
        _md_table(
            ["Item", "Value"],
            [
                ["Status", status["status"]],
                ["Coverage", status.get("coverage", "configured_persisted_logs_only")],
                ["Logs scanned", status["logs_scanned"]],
                ["Unapproved findings", status["unapproved_findings"]],
                ["Reviewed exceptions", status["reviewed_exceptions"]],
                ["Missing required logs", status["missing_required_logs"]],
            ],
        ),
        "",
        "## Reviewed Exception Caps",
        "",
        _md_table(["Exception", "Count", "Max", "Status", "Rationale"], exception_rows)
        if exception_rows else "No reviewed exceptions configured.",
        "",
        "## Excluded Logs",
        "",
        _md_table(["Log", "Rationale"], excluded_rows) if excluded_rows else "No excluded logs configured.",
        "",
        "## Unapproved Findings",
        "",
    ]
    if unapproved or missing:
        rows = [
            [f["file"], f["line"], f["rule_id"], f["severity"], f["message"]]
            for f in (missing + unapproved)[:50]
        ]
        lines.append(_md_table(["File", "Line", "Rule", "Severity", "Message"], rows))
        if len(missing) + len(unapproved) > 50:
            lines.append(f"\nFirst 50 shown of {len(missing) + len(unapproved)} unapproved/missing findings.")
    else:
        lines.append("No unapproved log findings.")
    lines.extend([
        "",
        "## Machine-Readable Outputs",
        "",
        "- `platform/log_cleanliness/log_cleanliness_status.json`",
        "- `platform/log_cleanliness/log_findings.csv`",
        "",
    ])
    report_path.write_text("\n".join(lines), encoding="utf-8")


def build_log_cleanliness(config_path: Path = DEFAULT_CONFIG, out_dir: Path = OUT_DIR, report_path: Path = REPORT) -> dict:
    config_path = config_path.resolve()
    out_dir = out_dir.resolve()
    report_path = report_path.resolve()
    config = _load_yaml(config_path)
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    fail_rules = _compile_rules(config.get("fail_patterns", []))
    exceptions = _compile_rules(config.get("reviewed_exceptions", []))

    findings: list[dict] = []
    required_specs = config.get("required_logs", [])
    optional_specs = config.get("optional_logs", [])
    scan_paths: list[Path] = []

    for spec in required_specs:
        matches = _expand(spec)
        if not matches:
            findings.append({
                "status": "MISSING_LOG",
                "file": spec,
                "line": "",
                "rule_id": "REQUIRED_LOG_MISSING",
                "severity": "major",
                "message": f"Required log is missing: {spec}",
                "rationale": "Configured execution evidence log must exist for the current validation run.",
                "owner": "platform_release",
            })
        scan_paths.extend(matches)
    for spec in optional_specs:
        scan_paths.extend(_expand(spec))

    unique_paths = []
    seen = set()
    for path in scan_paths:
        resolved = path.resolve()
        if resolved not in seen:
            seen.add(resolved)
            unique_paths.append(path)

    for path in unique_paths:
        findings.extend(_scan_log(path, fail_rules, exceptions))

    cap_rows = []
    cap_failures = []
    for exception in exceptions:
        count = sum(1 for f in findings if f["status"] == "REVIEWED_EXCEPTION" and f["rule_id"] == exception.get("id"))
        max_count = exception.get("max_count")
        cap_status = "PASS"
        if max_count is not None and count > int(max_count):
            cap_status = "FAIL"
            cap_failures.append(_finding(
                "UNAPPROVED",
                "config/log_cleanliness.yaml",
                "",
                {"id": f"{exception.get('id')}_CAP", "severity": "major",
                 "rationale": exception.get("rationale", "")},
                f"Reviewed exception {exception.get('id')} count {count} exceeds cap {max_count}",
            ))
        cap_rows.append({
            "id": exception.get("id", ""),
            "count": count,
            "max_count": max_count,
            "status": cap_status,
            "rationale": exception.get("rationale", ""),
        })
    findings.extend(cap_failures)

    unapproved = [f for f in findings if f["status"] == "UNAPPROVED"]
    missing = [f for f in findings if f["status"] == "MISSING_LOG"]
    reviewed = [f for f in findings if f["status"] == "REVIEWED_EXCEPTION"]
    status_value = "PASS" if not unapproved and not missing else "FAIL"
    status = {
        "status": status_value,
        "generated_at": generated_at,
        "config": _rel(config_path),
        "coverage": "configured_persisted_logs_only",
        "coverage_note": (
            "Scans only logs listed in config/log_cleanliness.yaml (required/optional). "
            "rscript/python stage stdout/stderr is not persisted by cibuild.py and is "
            "outside this gate; PASS means configured persisted logs are clean, not full "
            "pipeline stdout/stderr clean."
        ),
        "logs_scanned": len(unique_paths),
        "scanned_logs": [_rel(path) for path in unique_paths],
        "findings": len(findings),
        "unapproved_findings": len(unapproved),
        "reviewed_exceptions": len(reviewed),
        "missing_required_logs": len(missing),
        "reviewed_exception_caps": cap_rows,
        "excluded_logs": config.get("excluded_logs", []),
    }
    _write_outputs(status, findings, report_path, out_dir)
    return status


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Scan SAS/R logs for unapproved issues")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG))
    parser.add_argument("--out-dir", default=str(OUT_DIR))
    parser.add_argument("--report", default=str(REPORT))
    parser.add_argument("--allow-fail", action="store_true",
                        help="Write evidence but return zero even when findings fail the gate")
    args = parser.parse_args(argv)

    status = build_log_cleanliness(Path(args.config), Path(args.out_dir), Path(args.report))
    print(f"Log cleanliness status: {status['status']}")
    print(f"Logs scanned: {status['logs_scanned']}")
    print(f"Unapproved findings: {status['unapproved_findings']}")
    print(f"Reviewed exceptions: {status['reviewed_exceptions']}")
    print(f"Wrote {Path(args.out_dir) / 'log_cleanliness_status.json'}")
    if status["status"] != "PASS" and not args.allow_fail:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
