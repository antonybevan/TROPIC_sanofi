from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "validate_define", ROOT / "03_metadata/define/validate_define.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


def test_define_parser_disables_external_entity_resolution(tmp_path: Path) -> None:
    secret = tmp_path / "secret.txt"
    secret.write_text("must-not-be-read", encoding="utf-8")
    define = tmp_path / "define.xml"
    define.write_text(
        f'''<!DOCTYPE ODM [<!ENTITY local SYSTEM "{secret}">]>
<ODM xmlns="http://www.cdisc.org/ns/odm/v1.3"><Description>&local;</Description></ODM>''',
        encoding="utf-8",
    )
    problems, _checks = MODULE.validate(str(define))
    assert all("must-not-be-read" not in problem for problem in problems)


def test_define_parser_has_explicit_safe_parser_controls() -> None:
    source = (ROOT / "03_metadata/define/validate_define.py").read_text(encoding="utf-8")
    for setting in ("resolve_entities=False", "load_dtd=False", "no_network=True"):
        assert setting in source
