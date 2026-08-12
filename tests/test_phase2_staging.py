"""Data-free contract checks for the adopted F-042 PR staging handoff."""

from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    r_ingest = (ROOT / "04_analysis_datasets/programs/r/v_staging_ingest.R").read_text()
    sas_ingest = (ROOT / "04_analysis_datasets/programs/sas/L_staging_ingest.sas").read_text()
    f042 = (ROOT / "04_analysis_datasets/programs/r/f042_provisional_pain_derivation.R").read_text()

    assert re.search(r'domains\s*<-\s*c\([^)]*"pr"', r_ingest, re.S), (
        "R staging domain list must include PR"
    )
    assert "%transpose_supp(pr);" in sas_ingest, "SAS staging must materialize PR"
    assert re.search(r'domains\s*<-\s*c\([^)]*"sv"\s*\)', r_ingest, re.S), (
        "R staging domain list must include SV for governed visit dating"
    )
    assert "%transpose_supp(sv);" in sas_ingest, "SAS staging must materialize SV"
    assert 'f042_staging_dir(root)' in f042 and 'file.path(staging, "pr.rds")' in f042, (
        "F-042 derivation must resolve PR through the governed staging path"
    )
    assert 'read_sas(file.path(root, "01_source_data/real_sdtm/pr.sas7bdat"))' not in f042, (
        "F-042 derivation must not bypass the staging handoff"
    )
    assert 'file.path(staging, "sv.rds")' in f042, (
        "F-042 derivation must resolve SV through the governed staging path"
    )
    print("F-042 Phase 2 staging contract: PASS")


if __name__ == "__main__":
    main()
