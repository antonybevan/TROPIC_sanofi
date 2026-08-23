"""Small, data-free checks for the public repository surface.

These checks deliberately cover policy boundaries rather than generated clinical outputs.  They
make accidental reintroduction of credentials, local-only runtime files, or machine-specific links
visible in ordinary CI review.
"""

from __future__ import annotations

import csv
import importlib.util
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
_LOCAL_LINK = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
sys.path.insert(0, str(ROOT / "platform"))
from manifest import ManifestError, dataset_names, load_manifest  # noqa: E402


def _tracked_files() -> list[str]:
    result = subprocess.run(
        ["git", "-C", str(ROOT), "ls-files", "-z"],
        check=True,
        capture_output=True,
        text=False,
    )
    return [name for name in result.stdout.decode().split("\0") if name]


def test_sensitive_and_runtime_files_are_not_tracked() -> None:
    tracked = _tracked_files()
    forbidden_names = {
        "_authinfo",
        ".authinfo",
        "sascfg_personal.py",
        ".env",
    }
    forbidden_suffixes = (".pem", ".key", ".p12", ".pfx")
    violations = [
        name
        for name in tracked
        if Path(name).name in forbidden_names or Path(name).suffix.lower() in forbidden_suffixes
    ]
    assert violations == []


def test_local_only_surface_is_explicitly_ignored() -> None:
    ignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
    for pattern in (".hermes.md", "tmp/", "_authinfo", ".authinfo", "sascfg_personal.py", ".env"):
        assert pattern in ignore

    for local_path in ("_authinfo", "sascfg_personal.py"):
        result = subprocess.run(
            ["git", "-C", str(ROOT), "check-ignore", "-q", local_path],
            check=False,
        )
        assert result.returncode == 0, local_path


def test_active_markdown_has_no_machine_specific_file_urls() -> None:
    roots = [ROOT / "README.md", ROOT / "CONTRIBUTING.md", ROOT / "SECURITY.md"]
    roots.extend((ROOT / "docs").glob("*.md"))
    roots.extend((ROOT / "07_reviewer_explanation").glob("*.md"))
    offenders = []
    for path in roots:
        text = path.read_text(encoding="utf-8", errors="replace")
        if "file:///Users/" in text or "/Users/apple/Desktop/TROPIC" in text:
            offenders.append(str(path.relative_to(ROOT)))
    assert offenders == []


def test_active_markdown_relative_links_resolve() -> None:
    tracked = set(_tracked_files())
    roots = [ROOT / relative for relative in sorted(tracked) if relative.endswith(".md")]
    missing = []
    for source in roots:
        for target in _LOCAL_LINK.findall(source.read_text(encoding="utf-8", errors="replace")):
            target = target.strip().strip("<>").split("#", 1)[0]
            if not target or target.startswith(("http://", "https://", "mailto:", "data:")):
                continue
            resolved = (source.parent / target).resolve()
            try:
                relative = resolved.relative_to(ROOT).as_posix()
            except ValueError:
                missing.append(f"{source.relative_to(ROOT)} -> {target} (outside repository)")
                continue
            is_tracked = relative in tracked or any(
                item.startswith(relative.rstrip("/") + "/") for item in tracked
            )
            if not resolved.exists():
                missing.append(f"{source.relative_to(ROOT)} -> {target}")
            elif not is_tracked:
                missing.append(f"{source.relative_to(ROOT)} -> {target} (local-only/untracked)")
    assert missing == []


def test_present_local_credentials_have_restrictive_permissions() -> None:
    for relative in ("_authinfo", "sascfg_personal.py", ".authinfo", ".core_run/.env"):
        path = ROOT / relative
        if path.exists():
            assert path.stat().st_mode & 0o077 == 0, relative
    runtime = ROOT / ".core_run"
    if runtime.exists():
        assert runtime.stat().st_mode & 0o077 == 0


def test_core_runner_checks_ignored_credential_permissions_before_sourcing() -> None:
    runner = (ROOT / "platform/run_core_conformance.sh").read_text(encoding="utf-8")
    assert "stat.S_IMODE" in runner
    assert 'chmod 700 "$RUN"' in runner
    assert "Refusing insecure credential file permissions" in runner
    assert 'set -a' in runner


def test_manifest_dataset_names_are_safe_path_segments() -> None:
    assert dataset_names({"datasets": [{"name": "adsl"}, {"name": "ae_1"}]}) == [
        "adsl",
        "ae_1",
    ]
    for name in ("../escape", "a/b", "a b", "", "-bad"):
        try:
            dataset_names({"datasets": [{"name": name}]})
        except ManifestError:
            pass
        else:
            raise AssertionError(f"unsafe dataset name accepted: {name!r}")


def test_patient_level_generators_request_least_privilege_permissions() -> None:
    for relative, markers in {
        "platform/package_ectd.py": ("_copy_patient_file", "os.chmod(dest, 0o600)", "0o700"),
        "platform/export_datasetjson.py": ("os.chmod(out_dir, 0o700)", "os.chmod(out_path, 0o600)"),
        "platform/stage_p21_adam_inputs.py": ("temporary.chmod(0o700)", "target.chmod(0o600)"),
        "platform/materialize_ectd.py": ("os.chmod(dest, 0o600)", "os.chmod(os.path.dirname(dest), 0o700)"),
    }.items():
        source = (ROOT / relative).read_text(encoding="utf-8")
        for marker in markers:
            assert marker in source, (relative, marker)

    orchestrator = (ROOT / "platform/cibuild.py").read_text(encoding="utf-8")
    assert orchestrator.count("os.chmod(tmp_path, 0o600)") >= 1
    assert "os.chmod(tmp_file, 0o600)" in orchestrator


def test_core_conformance_runner_pins_source_and_package_versions() -> None:
    source = (ROOT / "platform/run_core_conformance.sh").read_text(encoding="utf-8")
    assert 'CORE_VERSION="0.16.0"' in source
    assert 'CORE_COMMIT="c78b05cad21379adf52c8fad5fe1760b826d1ef3"' in source
    assert '"cdisc-rules-engine==$CORE_VERSION"' in source


def test_manifest_infrastructure_stages_are_unique() -> None:
    manifest = load_manifest(path=ROOT / "config/study_manifest.yaml")
    stages = []
    for group in manifest.get("infrastructure_stages", {}).values():
        stages.extend(group or [])
    names = [stage["name"] for stage in stages]
    scripts = [stage["script"] for stage in stages]
    assert len(names) == len(set(names)), "duplicate infrastructure stage name"
    assert len(scripts) == len(set(scripts)), "duplicate infrastructure stage script"


def test_current_orphan_register_has_no_unresolved_cleanup_findings() -> None:
    register = (
        ROOT / "06_qc_evidence/audit/orphans_dangling_deadcode.csv"
    ).read_text(encoding="utf-8")
    assert ",CONFIRMED," not in register
    assert "tools/archive/" not in register
    for status in (
        "NO_UNINDEXED_PAYLOADS",
        "NO_FALSE_LISTING",
        "NO_STALE_OUTPUT",
        "RESOLVED_IN_DAG",
        "CLASSIFIED_ADDITIVE",
        "CLASSIFIED_OUT_OF_DAG",
    ):
        assert status in register


def test_no_listing_placeholder_is_tracked() -> None:
    tracked = _tracked_files()
    assert not [
        path
        for path in tracked
        if path.startswith("05_outputs/tfl/output/listings/") and (ROOT / path).exists()
    ]


def test_inventory_excludes_credential_bytes_and_restricts_outputs() -> None:
    source = (ROOT / "06_qc_evidence/audit/build_inventory.py").read_text(encoding="utf-8")
    assert '"sha256": "EXCLUDED"' in source
    assert source.index("if sensitive:") < source.index('with path.open("rb")')
    assert "os.chmod(out, 0o600)" in source
    assert "os.chmod(summary, 0o600)" in source

    module_path = ROOT / "06_qc_evidence/audit/build_inventory.py"
    spec = importlib.util.spec_from_file_location("tropic_build_inventory", module_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    for path in (Path("_authinfo"), Path("nested/.env"), Path("nested/prod.env")):
        assert module.is_sensitive(path)


def test_ars_binds_the_current_sap_authority() -> None:
    source = (ROOT / "platform/build_ars.py").read_text(encoding="utf-8")
    artifact = (ROOT / "05_outputs/ars/tropic_reporting_event.json").read_text(encoding="utf-8")
    for text in (source, artifact):
        assert "TROPIC SAP v4.0" in text
        assert "TROPIC_SAP_v4.0_industry_grade.docx" in text
        assert "TROPIC SAP v3.0" not in text


def test_traceability_matrix_has_exact_manifest_infrastructure_stage_numbers() -> None:
    manifest = load_manifest(path=ROOT / "config/study_manifest.yaml")
    matrix = (ROOT / "07_reviewer_explanation/guides/TRACEABILITY_MATRIX.md").read_text(
        encoding="utf-8"
    )
    groups = manifest.get("infrastructure_stages", {})
    expected: dict[str, int] = {}

    cursor = 1
    for stage in groups.get("pre", []) or []:
        expected[Path(stage["script"]).name] = cursor
        cursor += 1
    cursor += len(manifest.get("datasets", []) or [])
    for stage in groups.get("pre_sas", []) or []:
        expected[Path(stage["script"]).name] = cursor
        cursor += 1
    cursor += 1  # manifest-defined SAS Production executor stage
    for stage in groups.get("post", []) or []:
        expected[Path(stage["script"]).name] = cursor
        cursor += 1

    problems = []
    for script, expected_number in expected.items():
        rows = [
            int(match.group(1))
            for match in re.finditer(
                rf"^\|\s*(\d+)\s+\([^|\n]*\)\s*\|[^|\n]*`[^`]*{re.escape(script)}`",
                matrix,
                flags=re.MULTILINE,
            )
        ]
        if rows != [expected_number]:
            problems.append(f"{script}: expected stage {expected_number}, documented rows={rows}")
    assert problems == []


def test_ci_collects_the_complete_python_test_directory() -> None:
    workflow = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    assert "python3 -m pytest -q tests\n" in workflow


def test_release_verifier_uses_current_candidate_terminology() -> None:
    source = (ROOT / "scripts/verify_release.py").read_text(encoding="utf-8")
    assert "controlled-candidate release verification" in source
    assert "Path A release verification" not in source


def test_findings_register_has_exact_schema_and_unique_ids() -> None:
    path = ROOT / "06_qc_evidence/audit/findings_register.csv"
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
    expected = [
        "ID",
        "severity",
        "category",
        "status",
        "evidence",
        "standard_or_rule",
        "remediation",
        "effort",
        "disposition_class",
        "disposition_date",
        "disposition_note",
    ]
    assert reader.fieldnames == expected
    assert not [index for index, row in enumerate(rows, 2) if None in row]
    ids = [row["ID"] for row in rows]
    assert len(ids) == len(set(ids))
