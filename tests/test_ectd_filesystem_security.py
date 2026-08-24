"""Synthetic link-resolution regressions for the eCTD packaging boundary."""

from __future__ import annotations

import hashlib
import inspect
import os
import stat
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "platform"))

import build_ectd_backbone as backbone  # noqa: E402
import materialize_ectd as materialize  # noqa: E402
import package_ectd as package  # noqa: E402
import safe_filesystem as safe_fs  # noqa: E402
import validate_ectd_sequence as validator  # noqa: E402
from safe_filesystem import (  # noqa: E402
    UnsafePathError,
    atomic_write_text,
    open_regular,
    read_text,
    safe_copy_file,
    safe_rmtree,
    walk_regular_files,
)


def _regular_source_and_destination(tmp_path: Path) -> tuple[Path, Path, Path]:
    source_root = tmp_path / "source"
    destination_root = tmp_path / "destination"
    source_root.mkdir()
    destination_root.mkdir()
    source = source_root / "dataset.xpt"
    source.write_bytes(b"controlled dataset")
    return source_root, destination_root, source


def _copy_patient_file(
    source: Path,
    destination: Path,
    *,
    source_root: Path,
    destination_root: Path,
) -> None:
    package._copy_patient_file(
        source,
        destination,
        source_root=source_root,
        destination_root=destination_root,
    )


def _configure_materializer(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> dict[str, Path]:
    package_root = tmp_path / "package"
    m5_root = package_root / "m5"
    ectd_root = package_root / "ectd"
    sequence = ectd_root / "0000"
    platform_root = tmp_path / "platform"
    for directory in (m5_root, sequence, platform_root):
        directory.mkdir(parents=True, exist_ok=True)
    paths = {
        "package_root": package_root,
        "m5_root": m5_root,
        "ectd_root": ectd_root,
        "sequence": sequence,
        "index": sequence / "index.xml",
        "platform_root": platform_root,
        "cache": platform_root / ".materialize_ectd_cache.json",
    }
    monkeypatch.setattr(materialize, "PACKAGE_ROOT", package_root)
    monkeypatch.setattr(materialize, "M5_ROOT", m5_root)
    monkeypatch.setattr(materialize, "ECTD_ROOT", ectd_root)
    monkeypatch.setattr(materialize, "SEQ", sequence)
    monkeypatch.setattr(materialize, "INDEX", paths["index"])
    monkeypatch.setattr(materialize, "HERE", platform_root)
    monkeypatch.setattr(materialize, "CACHE_FILE", paths["cache"])
    return paths


def _write_index(index: Path, href: str, payload: bytes) -> None:
    checksum = hashlib.md5(payload).hexdigest()
    index.write_text(
        '<ectd xmlns:xlink="urn:test">'
        f'<leaf ID="L1" xlink:href="{href}" checksum-type="MD5" '
        f'checksum="{checksum}" />'
        "</ectd>",
        encoding="utf-8",
    )


def test_package_rejects_symlinked_source_file(tmp_path: Path) -> None:
    source_root, destination_root, _source = _regular_source_and_destination(tmp_path)
    victim = tmp_path / "patient-record.txt"
    victim.write_bytes(b"outside patient data")
    linked_source = source_root / "linked.xpt"
    linked_source.symlink_to(victim)

    with pytest.raises(UnsafePathError, match="symlink"):
        _copy_patient_file(
            linked_source,
            destination_root / "copied.xpt",
            source_root=source_root,
            destination_root=destination_root,
        )

    assert not (destination_root / "copied.xpt").exists()
    assert victim.read_bytes() == b"outside patient data"


def test_package_rejects_symlinked_source_ancestor(tmp_path: Path) -> None:
    source_root, destination_root, _source = _regular_source_and_destination(tmp_path)
    outside = tmp_path / "outside-source"
    outside.mkdir()
    (outside / "patient.xpt").write_bytes(b"outside patient data")
    (source_root / "linked-directory").symlink_to(outside, target_is_directory=True)

    with pytest.raises(UnsafePathError, match="symlink"):
        _copy_patient_file(
            source_root / "linked-directory/patient.xpt",
            destination_root / "copied.xpt",
            source_root=source_root,
            destination_root=destination_root,
        )

    assert not (destination_root / "copied.xpt").exists()


def test_package_rejects_symlinked_destination_file_without_touching_target(
    tmp_path: Path,
) -> None:
    source_root, destination_root, source = _regular_source_and_destination(tmp_path)
    victim = tmp_path / "outside-destination.txt"
    victim.write_bytes(b"preserve me")
    destination = destination_root / "dataset.xpt"
    destination.symlink_to(victim)

    with pytest.raises(UnsafePathError, match="symlink"):
        _copy_patient_file(
            source,
            destination,
            source_root=source_root,
            destination_root=destination_root,
        )

    assert destination.is_symlink()
    assert victim.read_bytes() == b"preserve me"


def test_package_rejects_symlinked_destination_ancestor(tmp_path: Path) -> None:
    source_root, destination_root, source = _regular_source_and_destination(tmp_path)
    outside = tmp_path / "outside-destination"
    outside.mkdir()
    (destination_root / "linked-directory").symlink_to(outside, target_is_directory=True)

    with pytest.raises(UnsafePathError, match="symlink"):
        _copy_patient_file(
            source,
            destination_root / "linked-directory/dataset.xpt",
            source_root=source_root,
            destination_root=destination_root,
        )

    assert not (outside / "dataset.xpt").exists()


def test_descriptor_read_pins_ancestor_during_symlink_swap(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    source_root = tmp_path / "source"
    source_parent = source_root / "slot"
    outside = tmp_path / "outside"
    source_parent.mkdir(parents=True)
    outside.mkdir()
    source = source_parent / "patient.xpt"
    source.write_text("authorized", encoding="utf-8")
    (outside / source.name).write_text("outside", encoding="utf-8")

    original_open = safe_fs.os.open
    swapped = False

    def racing_open(path, flags, *args, **kwargs):
        nonlocal swapped
        if os.fspath(path).endswith(source.name) and not swapped:
            swapped = True
            source_parent.rename(source_root / "slot-original")
            source_parent.symlink_to(outside, target_is_directory=True)
        return original_open(path, flags, *args, **kwargs)

    monkeypatch.setattr(safe_fs.os, "open", racing_open)

    assert read_text(source, source_root) == "authorized"
    assert swapped
    assert (outside / source.name).read_text(encoding="utf-8") == "outside"


def test_descriptor_read_rejects_in_place_source_change(tmp_path: Path) -> None:
    source_root = tmp_path / "source"
    source_root.mkdir()
    source = source_root / "patient.xpt"
    source.write_bytes(b"authorized")

    with pytest.raises(UnsafePathError, match="changed while being read"):
        with open_regular(source, source_root, binary=True) as stream:
            assert stream.read() == b"authorized"
            # The inode and pathname stay fixed; only the bytes change.
            source.write_bytes(b"substituted")


def test_atomic_copy_rejects_in_place_source_change_before_promotion(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    source_root, destination_root, source = _regular_source_and_destination(tmp_path)
    destination = destination_root / "dataset.xpt"
    destination.write_bytes(b"preserve prior controlled output")
    original_copy = safe_fs.shutil.copyfileobj

    def racing_copy(source_stream, destination_stream, length):
        original_copy(source_stream, destination_stream, length=length)
        source.write_bytes(b"substituted patient data")

    monkeypatch.setattr(safe_fs.shutil, "copyfileobj", racing_copy)

    with pytest.raises(UnsafePathError, match="changed while being copied"):
        safe_copy_file(
            source,
            destination,
            source_root=source_root,
            destination_root=destination_root,
        )

    assert destination.read_bytes() == b"preserve prior controlled output"


def test_pdf_renderer_never_hands_final_package_path_to_third_party_writers() -> None:
    source = inspect.getsource(package.md_to_pdf)
    assert "TemporaryDirectory" in source
    assert "safe_copy_file(" in source
    assert "os.replace(" not in source
    assert "cwd=temporary_root" in source


def test_atomic_write_pins_destination_ancestor_during_symlink_swap(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    destination_root = tmp_path / "destination"
    destination_parent = destination_root / "slot"
    outside = tmp_path / "outside"
    destination_parent.mkdir(parents=True)
    outside.mkdir()
    target = destination_parent / "release.txt"
    outside_target = outside / target.name
    outside_target.write_text("preserve", encoding="utf-8")

    original_open = safe_fs.os.open
    swapped = False

    def racing_open(path, flags, *args, **kwargs):
        nonlocal swapped
        if os.fspath(path).startswith(".tropic-") and not swapped:
            swapped = True
            destination_parent.rename(destination_root / "slot-original")
            destination_parent.symlink_to(outside, target_is_directory=True)
        return original_open(path, flags, *args, **kwargs)

    monkeypatch.setattr(safe_fs.os, "open", racing_open)

    atomic_write_text(target, "controlled", destination_root)

    assert swapped
    assert outside_target.read_text(encoding="utf-8") == "preserve"
    assert (destination_root / "slot-original/release.txt").read_text(
        encoding="utf-8"
    ) == "controlled"


def test_tree_walk_fails_closed_when_a_subtree_cannot_be_enumerated(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    controlled = tmp_path / "controlled"
    hidden = controlled / "hidden"
    hidden.mkdir(parents=True)
    (hidden / "unexpected.txt").write_text("must not be skipped", encoding="utf-8")

    original_listdir = safe_fs.os.listdir
    calls = 0

    def denied_subtree(path):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise PermissionError("synthetic enumeration denial")
        return original_listdir(path)

    monkeypatch.setattr(safe_fs.os, "listdir", denied_subtree)

    with pytest.raises(UnsafePathError, match="cannot enumerate controlled directory"):
        walk_regular_files(controlled)


def test_backbone_collect_rejects_link_anywhere_in_module_five(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    package_root = tmp_path / "package"
    m5_root = package_root / "m5"
    outside = tmp_path / "outside-programs"
    m5_root.mkdir(parents=True)
    outside.mkdir()
    (outside / "analysis.sas").write_text("%put private;", encoding="utf-8")
    (m5_root / "programs").symlink_to(outside, target_is_directory=True)
    monkeypatch.setattr(backbone, "PACKAGE_ROOT", package_root)
    monkeypatch.setattr(backbone, "M5_SRC", m5_root)

    with pytest.raises(UnsafePathError, match="symlink"):
        backbone.collect()


def test_backbone_preserves_target_of_symlinked_index_control_file(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    package_root = tmp_path / "package"
    m5_root = package_root / "m5"
    ectd_root = package_root / "ectd"
    sequence = ectd_root / "0000"
    program = m5_root / "analysis/adam/programs/example.sas"
    program.parent.mkdir(parents=True)
    program.write_text("%put example;", encoding="utf-8")
    sequence.mkdir(parents=True)
    victim = tmp_path / "outside-index.xml"
    victim.write_text("outside control", encoding="utf-8")
    (sequence / "index.xml").symlink_to(victim)

    monkeypatch.setattr(backbone, "PACKAGE_ROOT", package_root)
    monkeypatch.setattr(backbone, "M5_SRC", m5_root)
    monkeypatch.setattr(backbone, "ECTD_ROOT", ectd_root)
    monkeypatch.setattr(backbone, "SEQ_ROOT", sequence)
    monkeypatch.setattr(backbone, "SUPPORT_FILES", {})

    with pytest.raises(UnsafePathError, match="symlink"):
        backbone.main()

    assert (sequence / "index.xml").is_symlink()
    assert victim.read_text(encoding="utf-8") == "outside control"


def test_materializer_rejects_symlinked_module_five_source(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    paths = _configure_materializer(monkeypatch, tmp_path)
    payload = b"outside patient data"
    victim = tmp_path / "outside-source.xpt"
    victim.write_bytes(payload)
    source = paths["m5_root"] / "data/patient.xpt"
    source.parent.mkdir()
    source.symlink_to(victim)
    _write_index(paths["index"], "m5/data/patient.xpt", payload)

    with pytest.raises(UnsafePathError, match="symlink"):
        materialize.main()

    assert not (paths["sequence"] / "m5/data/patient.xpt").exists()


def test_materializer_preserves_normal_copy_layout_and_permissions(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    paths = _configure_materializer(monkeypatch, tmp_path)
    payload = b"controlled dataset"
    source = paths["m5_root"] / "data/patient.xpt"
    source.parent.mkdir()
    source.write_bytes(payload)
    _write_index(paths["index"], "m5/data/patient.xpt", payload)
    monkeypatch.setattr(
        validator,
        "validate_sequence",
        lambda require_all_leaves=True: {"status": "PASS"},
    )

    materialize.main()

    destination = paths["sequence"] / "m5/data/patient.xpt"
    assert destination.read_bytes() == payload
    assert stat.S_IMODE(destination.stat().st_mode) == 0o600
    assert stat.S_IMODE(destination.parent.stat().st_mode) == 0o700
    assert paths["cache"].is_file()


def test_materializer_rejects_symlinked_destination_ancestor(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    paths = _configure_materializer(monkeypatch, tmp_path)
    payload = b"controlled dataset"
    source = paths["m5_root"] / "data/patient.xpt"
    source.parent.mkdir()
    source.write_bytes(payload)
    outside = tmp_path / "outside-sequence"
    outside.mkdir()
    (paths["sequence"] / "m5").symlink_to(outside, target_is_directory=True)
    _write_index(paths["index"], "m5/data/patient.xpt", payload)

    with pytest.raises(UnsafePathError, match="symlink"):
        materialize.main()

    assert not (outside / "data/patient.xpt").exists()


def test_sequence_cleanup_rejects_symlinked_root_and_preserves_target(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    ectd_root = tmp_path / "ectd"
    outside_sequence = tmp_path / "outside-sequence"
    ectd_root.mkdir()
    outside_sequence.mkdir()
    victim = outside_sequence / "keep.txt"
    victim.write_text("do not delete", encoding="utf-8")
    linked_sequence = ectd_root / "0000"
    linked_sequence.symlink_to(outside_sequence, target_is_directory=True)
    monkeypatch.setattr(materialize, "ECTD_ROOT", ectd_root)
    monkeypatch.setattr(materialize, "SEQ", linked_sequence)

    with pytest.raises(UnsafePathError, match="symlink"):
        materialize.purge_unindexed_sequence_files([])

    assert linked_sequence.is_symlink()
    assert victim.read_text(encoding="utf-8") == "do not delete"


def test_recursive_cleanup_rejects_symlinked_tree_and_preserves_target(
    tmp_path: Path,
) -> None:
    package_root = tmp_path / "package"
    outside = tmp_path / "outside-tree"
    package_root.mkdir()
    outside.mkdir()
    victim = outside / "keep.txt"
    victim.write_text("do not delete", encoding="utf-8")
    linked_tree = package_root / "m5"
    linked_tree.symlink_to(outside, target_is_directory=True)

    with pytest.raises(UnsafePathError, match="symlink"):
        safe_rmtree(linked_tree, package_root)

    assert linked_tree.is_symlink()
    assert victim.read_text(encoding="utf-8") == "do not delete"


def test_cache_write_rejects_symlink_and_preserves_target(tmp_path: Path) -> None:
    cache_root = tmp_path / "platform"
    cache_root.mkdir()
    victim = tmp_path / "outside-cache.json"
    victim.write_text('{"preserve": true}\n', encoding="utf-8")
    cache = cache_root / ".materialize_ectd_cache.json"
    cache.symlink_to(victim)

    with pytest.raises(UnsafePathError, match="symlink"):
        materialize._save_cache({"changed": True}, path=cache, root=cache_root)

    assert cache.is_symlink()
    assert victim.read_text(encoding="utf-8") == '{"preserve": true}\n'


def test_validator_fails_closed_on_symlinked_sequence_entry(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    ectd_root = tmp_path / "ectd"
    sequence = ectd_root / "0000"
    sequence.mkdir(parents=True)
    victim = tmp_path / "outside-patient.xpt"
    victim.write_bytes(b"outside patient data")
    (sequence / "patient.xpt").symlink_to(victim)
    monkeypatch.setattr(validator, "ECTD_ROOT", ectd_root)
    monkeypatch.setattr(validator, "SEQ", sequence)
    monkeypatch.setattr(validator, "INDEX", sequence / "index.xml")
    monkeypatch.setattr(validator, "INDEX_MD5", sequence / "index-md5.txt")
    monkeypatch.setattr(validator, "RUN_RECORD", ectd_root / "RUN_RECORD.md")

    result = validator.validate_sequence(validate_dtd=False)

    assert result["status"] == "FAIL"
    assert any("symlink" in problem for problem in result["problems"])
    assert victim.read_bytes() == b"outside patient data"
