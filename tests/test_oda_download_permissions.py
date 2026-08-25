"""Least-privilege regression checks for local SAS/ODA artifacts."""

from __future__ import annotations

import importlib.util
import os
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("cibuild_permissions", ROOT / "platform/cibuild.py")
cibuild = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(cibuild)


def test_atomic_oda_download_promotes_a_private_file(tmp_path: Path) -> None:
    class FakeSas:
        def download(self, local_path: str, remote_path: str) -> None:
            del remote_path
            path = Path(local_path)
            path.write_bytes(b"patient-derived-test-payload")
            path.chmod(0o644)

    destination = tmp_path / "adsl_prod.xpt"
    cibuild._atomic_download(FakeSas(), str(destination), "/remote/adsl_prod.xpt")

    assert destination.read_bytes() == b"patient-derived-test-payload"
    assert destination.stat().st_mode & 0o077 == 0
    assert not Path(str(destination) + ".part").exists()


def test_simulated_sas_copy_promotes_a_private_file(tmp_path: Path) -> None:
    adam = tmp_path / "04_analysis_datasets/adam"
    adam.mkdir(parents=True)
    validation = adam / "adsl_v.xpt"
    validation.write_bytes(b"validation-test-payload")
    validation.chmod(0o644)

    previous = Path.cwd()
    try:
        os.chdir(tmp_path)
        cibuild._sim_byte_copy(["adsl"])
    finally:
        os.chdir(previous)

    production = adam / "adsl_prod.xpt"
    assert production.read_bytes() == b"validation-test-payload"
    assert production.stat().st_mode & 0o077 == 0
