from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
_SPEC = importlib.util.spec_from_file_location(
    "stage_p21_adam_inputs",
    ROOT / "platform/stage_p21_adam_inputs.py",
)
assert _SPEC and _SPEC.loader
_MODULE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)
stage_inputs = _MODULE.stage_inputs


def _write_xpt_fixture(path: Path, member_name: str) -> None:
    body = bytearray(b" " * 640)
    signature = b"HEADER RECORD*******LIBRARY HEADER RECORD"
    body[: len(signature)] = signature
    encoded = member_name.encode("ascii").ljust(8, b" ")
    body[408:416] = encoded
    path.write_bytes(body)


def _source_set(path: Path, *, bad_member: str | None = None) -> None:
    path.mkdir()
    for dataset in _MODULE.DATASETS:
        member = bad_member if dataset == "adlb" and bad_member else dataset.upper()
        _write_xpt_fixture(path / f"{dataset}_prod.xpt", member)


def test_staging_uses_submission_names_without_changing_bytes(tmp_path: Path):
    source = tmp_path / "source"
    output = tmp_path / "p21-inputs"
    _source_set(source)

    payload = stage_inputs(source, output)

    assert payload["status"] == "PASS"
    assert payload["content_transformations"] == 0
    assert {path.name for path in output.iterdir()} == {
        f"{dataset}.xpt" for dataset in _MODULE.DATASETS
    }
    for row in payload["datasets"]:
        source_path = source / row["source_filename"]
        staged_path = output / row["validator_filename"]
        assert staged_path.read_bytes() == source_path.read_bytes()
        assert row["sha256"] == hashlib.sha256(staged_path.read_bytes()).hexdigest()
        assert row["internal_member_name"] == row["dataset"]
        assert row["byte_identical"] is True


def test_staging_rejects_wrong_internal_member_before_writing(tmp_path: Path):
    source = tmp_path / "source"
    output = tmp_path / "p21-inputs"
    _source_set(source, bad_member="BADNAME")

    with pytest.raises(ValueError, match="internal member"):
        stage_inputs(source, output)

    assert not output.exists()


def test_staging_refuses_to_merge_into_existing_directory(tmp_path: Path):
    source = tmp_path / "source"
    output = tmp_path / "p21-inputs"
    _source_set(source)
    output.mkdir()

    with pytest.raises(FileExistsError, match="fresh controlled directory"):
        stage_inputs(source, output)
