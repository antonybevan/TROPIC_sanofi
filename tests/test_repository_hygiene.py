"""Small, data-free checks for the public repository surface.

These checks deliberately cover policy boundaries rather than generated clinical outputs.  They
make accidental reintroduction of credentials, local-only runtime files, or machine-specific links
visible in ordinary CI review.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
_LOCAL_LINK = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
sys.path.insert(0, str(ROOT / "platform"))
from manifest import ManifestError, dataset_names  # noqa: E402


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
    roots = [ROOT / "README.md", ROOT / "CONTRIBUTING.md", ROOT / "SECURITY.md"]
    roots.extend((ROOT / "docs").glob("*.md"))
    roots.extend((ROOT / "07_reviewer_explanation").glob("*.md"))
    missing = []
    for source in roots:
        for target in _LOCAL_LINK.findall(source.read_text(encoding="utf-8", errors="replace")):
            target = target.strip().strip("<>").split("#", 1)[0]
            if not target or target.startswith(("http://", "https://", "mailto:", "data:")):
                continue
            if not (source.parent / target).exists():
                missing.append(f"{source.relative_to(ROOT)} -> {target}")
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


def test_core_conformance_runner_pins_source_and_package_versions() -> None:
    source = (ROOT / "platform/run_core_conformance.sh").read_text(encoding="utf-8")
    assert 'CORE_VERSION="0.16.0"' in source
    assert 'CORE_COMMIT="c78b05cad21379adf52c8fad5fe1760b826d1ef3"' in source
    assert '"cdisc-rules-engine==$CORE_VERSION"' in source
