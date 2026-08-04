import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFINE = ROOT / "03_metadata/define/define.xml"
MODULE_PATH = ROOT / "platform/define_arm_contract.py"
SPEC = importlib.util.spec_from_file_location("tropic_define_arm_contract", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
evaluate = MODULE.evaluate


def failures(path: Path) -> set[str]:
    return {
        str(check["name"])
        for check in evaluate(path)
        if not check["ok"]
    }


def test_current_define_arm_contract_passes():
    assert failures(DEFINE) == set()


def test_ttpain_result_negative_control(tmp_path):
    text = DEFINE.read_text(encoding="utf-8")
    broken = text.replace(
        'OID="AR.TTPAIN.COX"',
        'OID="AR.TTPAIN.COX.BROKEN"',
        1,
    )
    path = tmp_path / "define_missing_ttpain_result.xml"
    path.write_text(broken, encoding="utf-8")
    assert "define.arm_TTPAIN_result" in failures(path)


def test_ttumor_population_negative_control(tmp_path):
    text = DEFINE.read_text(encoding="utf-8")
    broken = text.replace(
        "Time to Tumor Progression - ITT comparative demonstration",
        "Time to Tumor Progression (measurable-disease subpopulation) - "
        "comparative demonstration",
        1,
    )
    path = tmp_path / "define_stale_ttumor_population.xml"
    path.write_text(broken, encoding="utf-8")
    assert "define.arm_TTUMOR_ITT" in failures(path)


def test_result_display_disclosure_negative_control(tmp_path):
    text = DEFINE.read_text(encoding="utf-8")
    broken = text.replace(
        "Path A limitation: CbzP is synthetic/reconstructed and TFL-only; "
        "comparative results are non-confirmatory and are not submission evidence.",
        "Comparator limitation omitted.",
        1,
    )
    path = tmp_path / "define_missing_disclosure.xml"
    path.write_text(broken, encoding="utf-8")
    assert "define.arm_CbzP_disclosure" in failures(path)
