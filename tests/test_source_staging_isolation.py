"""Data-free controls for the immutable-source / writable-staging boundary."""

from __future__ import annotations

from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]


def _is_within(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def test_governed_paths_are_disjoint() -> None:
    cfg = yaml.safe_load((ROOT / "config/study_config.yaml").read_text(encoding="utf-8"))
    source = (ROOT / cfg["SOURCE_SDTM_PATH"]).resolve()
    staging = (ROOT / cfg["STAGING_PATH"]).resolve()
    assert source != staging
    assert not _is_within(staging, source), "staging must not descend from immutable source"


def test_sas_runtime_enforces_distinct_librefs() -> None:
    config = (ROOT / "04_analysis_datasets/programs/sas/00_config.sas").read_text(encoding="utf-8")
    assert "access=readonly" in config.lower()
    assert "&SOURCE_SDTM_PATH." in config
    assert "&STAGING_PATH." in config
    assert "[SOURCE-ISOLATION]" in config
    assert "%qsysfunc(compare(" in config
    assert "%if %upcase(%superq(_realsdtm_path))" not in config


def test_r_runtime_enforces_distinct_paths() -> None:
    ingest = (ROOT / "04_analysis_datasets/programs/r/v_staging_ingest.R").read_text(encoding="utf-8")
    assert "SOURCE_SDTM_PATH" in ingest
    assert "STAGING_PATH" in ingest
    assert "startsWith(staging_real, source_prefix)" in ingest
    assert "01_source_data/real_sdtm/staging" not in ingest


def test_staging_patient_data_are_ignored() -> None:
    ignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
    assert "04_analysis_datasets/staging/" in ignore


if __name__ == "__main__":
    test_governed_paths_are_disjoint()
    test_sas_runtime_enforces_distinct_librefs()
    test_r_runtime_enforces_distinct_paths()
    test_staging_patient_data_are_ignored()
    print("Source/staging isolation controls: PASS")
