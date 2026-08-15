"""Regression tests for audited math and fail-closed release contracts."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest


ROOT = Path(__file__).resolve().parents[1]


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


SIM = _load("simulation_precision_hardening", ROOT / "platform/simulation_precision.py")
TTE = _load("tte_utils_hardening", ROOT / "platform/tte_utils.py")


def test_summarize_trial_rejects_fractional_binary_inputs() -> None:
    with pytest.raises(SIM.ProtocolError, match="events must contain only 0/1"):
        SIM.summarize_trial(
            [1, 2, 3, 4, 5, 6],
            [0.5, 1, 0, 1, 0, 1],
            [0, 0, 1, 1, 0, 1],
        )

    with pytest.raises(SIM.ProtocolError, match="treatment must contain only 0/1"):
        SIM.summarize_trial(
            [1, 2, 3, 4, 5, 6],
            [1, 1, 0, 1, 0, 1],
            [0, 0, 0.9, 1, 0, 1],
        )


def test_logrank_rejects_ties_for_no_tie_algorithm() -> None:
    with pytest.raises(SIM.ProtocolError, match="tied times are unsupported"):
        SIM.logrank_batch(
            np.array([[1.0, 1.0, 2.0, 3.0]]),
            np.array([[1, 1, 1, 0]], dtype=int),
            np.array([0, 1, 0, 1], dtype=int),
        )


@pytest.mark.parametrize(
    ("times", "events"),
    [
        (np.array([-1.0, 2.0, 3.0]), np.array([1, 0, 1])),
        (np.array([np.nan, 2.0, 3.0]), np.array([1, 0, 1])),
        (np.array([1.0, 2.0, 3.0]), np.array([0, 2, 1])),
    ],
)
def test_km_rejects_invalid_time_or_event_domain(times: np.ndarray, events: np.ndarray) -> None:
    with pytest.raises(ValueError):
        TTE.km_median_days(times, events)


def test_missing_condition_values_cannot_match_string_nan() -> None:
    df = pd.DataFrame(
        {
            "PARAMCD": ["OS", "OS"],
            "TRT01P": [np.nan, "MP"],
            "AVAL": [1.0, 2.0],
            "CNSR": [0, 1],
        }
    )
    with pytest.raises(ValueError, match="No records remain"):
        TTE.tte_analysis_set(df, "OS", [{"variable": "TRT01P", "value": ["nan"]}])


def test_tte_rejects_negative_analysis_time() -> None:
    df = pd.DataFrame(
        {
            "PARAMCD": ["OS"],
            "TRT01P": ["MP"],
            "AVAL": [-1.0],
            "CNSR": [0],
        }
    )
    with pytest.raises(ValueError, match="invalid AVAL"):
        TTE.tte_analysis_set(df, "OS", [{"variable": "TRT01P", "value": ["MP"]}])


def test_sas_and_local_log_controls_are_fail_closed() -> None:
    adtte = (ROOT / "04_analysis_datasets/programs/sas/A_adtte_generation.sas").read_text()
    adsl = (ROOT / "04_analysis_datasets/programs/sas/A_adsl_generation.sas").read_text()
    v_adsl = (ROOT / "04_analysis_datasets/programs/r/v_adsl_validation.R").read_text()
    cibuild = (ROOT / "platform/cibuild.py").read_text()

    assert adtte.count("%abort cancel;") >= 3
    assert "duplicate USUBJID/PARAMCD keys" in adtte
    assert "count(distinct usubjid)" in adsl
    assert "anyDuplicated(adsl$USUBJID)" in v_adsl
    assert 'SAS_MASTER_LOG = "04_analysis_datasets/programs/sas/oda_master_driver.log"' in cibuild
    assert '"-log", SAS_MASTER_LOG' in cibuild
