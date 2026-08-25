#!/usr/bin/env python3
"""Stage ADaM XPTs for Pinnacle 21 under submission-standard filenames.

The production pipeline retains ``*_prod.xpt`` filenames to distinguish the SAS
production track from the independent R validation track. Pinnacle 21 derives
the ADaM domain identity from the source filename, so those engineering suffixes
must not be presented to the validator. This utility makes byte-identical copies
named ``adae.xpt`` through ``adtte.xpt``, verifies each XPT's internal member
name, and fails closed on a contaminated or pre-existing destination.

The output contains patient-level data. A destination inside this repository is
therefore permitted only beneath the gitignored ``.p21`` runtime directory.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATASETS = ("adae", "adcm", "adex", "adlb", "adrs", "adsl", "adtte")
XPT_LIBRARY_HEADER = b"HEADER RECORD*******LIBRARY HEADER RECORD"
XPT_MEMBER_NAME_OFFSET = 408
XPT_MEMBER_NAME_LENGTH = 8


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _xpt_member_name(path: Path) -> str:
    with path.open("rb") as handle:
        header = handle.read(len(XPT_LIBRARY_HEADER))
        if header != XPT_LIBRARY_HEADER:
            raise ValueError(f"{path.name}: not a SAS XPORT v5 library header")
        handle.seek(XPT_MEMBER_NAME_OFFSET)
        raw_name = handle.read(XPT_MEMBER_NAME_LENGTH)
    if len(raw_name) != XPT_MEMBER_NAME_LENGTH:
        raise ValueError(f"{path.name}: truncated before the XPT member name")
    try:
        return raw_name.decode("ascii").strip().upper()
    except UnicodeDecodeError as exc:
        raise ValueError(f"{path.name}: non-ASCII XPT member name") from exc


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def stage_inputs(source_dir: Path, output_dir: Path) -> dict:
    source_dir = source_dir.resolve()
    output_dir = output_dir.resolve()
    runtime_root = (ROOT / ".p21").resolve()

    if _is_relative_to(output_dir, ROOT) and not _is_relative_to(output_dir, runtime_root):
        raise ValueError(
            "patient-level staging inside the repository is allowed only beneath .p21"
        )
    if output_dir.exists():
        raise FileExistsError(
            f"destination already exists; choose a fresh controlled directory: {output_dir}"
        )

    preflight: list[tuple[str, Path, str, int]] = []
    for dataset in DATASETS:
        source = source_dir / f"{dataset}_prod.xpt"
        if not source.is_file():
            raise FileNotFoundError(f"missing production transport: {source}")
        member_name = _xpt_member_name(source)
        if member_name != dataset.upper():
            raise ValueError(
                f"{source.name}: internal member {member_name!r} != {dataset.upper()!r}"
            )
        preflight.append((dataset, source, _sha256(source), source.stat().st_size))

    output_dir.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(
        tempfile.mkdtemp(prefix=".p21-adam-staging-", dir=str(output_dir.parent))
    )
    temporary.chmod(0o700)
    rows: list[dict] = []
    try:
        for dataset, source, source_sha256, size_bytes in preflight:
            target = temporary / f"{dataset}.xpt"
            shutil.copyfile(source, target)
            target.chmod(0o600)
            target_sha256 = _sha256(target)
            if target_sha256 != source_sha256 or target.stat().st_size != size_bytes:
                raise RuntimeError(f"byte verification failed while staging {dataset.upper()}")
            if _xpt_member_name(target) != dataset.upper():
                raise RuntimeError(f"member-name verification failed for {target.name}")
            rows.append(
                {
                    "dataset": dataset.upper(),
                    "source_filename": source.name,
                    "validator_filename": target.name,
                    "internal_member_name": dataset.upper(),
                    "size_bytes": size_bytes,
                    "sha256": source_sha256,
                    "byte_identical": True,
                }
            )

        actual = {path.name for path in temporary.iterdir() if path.is_file()}
        expected = {f"{dataset}.xpt" for dataset in DATASETS}
        if actual != expected:
            raise RuntimeError(
                f"staging scope mismatch: actual={sorted(actual)} expected={sorted(expected)}"
            )
        os.replace(temporary, output_dir)
    except Exception:
        shutil.rmtree(temporary, ignore_errors=True)
        raise

    return {
        "schema_version": "1.0",
        "status": "PASS",
        "purpose": "Pinnacle 21 ADaM exact-byte filename staging",
        "source_directory": str(source_dir),
        "output_directory": str(output_dir),
        "content_transformations": 0,
        "datasets": rows,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source-dir",
        type=Path,
        default=ROOT / "04_analysis_datasets/adam",
        help="directory containing the seven SAS *_prod.xpt artifacts",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT / ".p21/adam-inputs",
        help="fresh destination for standard-named validator inputs",
    )
    args = parser.parse_args(argv)
    payload = stage_inputs(args.source_dir, args.output_dir)
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
