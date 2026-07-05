"""
Unit tests for the ODA resilience layer (broker + seed). No Java, network, or live ODA needed —
every collaborator is injected. Run:  python3 06_telemetry/test_oda_broker.py
Covers acceptance criteria §7: earned-mode (probe), teardown on failed spawn, fail-fast classes,
backoff-not-blind-loop, idempotent seed, unverified-library detection.
"""
import os
import sys
import json
import glob
import signal
import threading
import tempfile
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import oda_broker as B
import seed_sdtm as S
import export_datasetjson as DJ
import date_precision_sensitivity as DPS
import build_ars as ARS
import tte_utils as TU
import build_usdm as USDM
import adam_conf_parse_define as ADEF
import ct_cross_validation as CTV
import generate_config as GC


class FakeClock:
    """Time advances ONLY via sleep — deterministic budget control."""
    def __init__(self): self.t = 0.0
    def read(self): return self.t
    def sleep(self, d): self.t += d


class FakeSas:
    def __init__(self, remote_manifest=None, nobs_log=""):
        self.uploaded, self.ended = [], False
        self.remote_manifest, self.nobs_log = remote_manifest, nobs_log
    def upload(self, local, remote, **kw): self.uploaded.append(os.path.basename(remote))
    def download(self, local, remote, **kw):
        if self.remote_manifest is None:
            raise RuntimeError("file not found on ODA")
        with open(local, "w") as f:
            json.dump(self.remote_manifest, f)
    def submit(self, code):
        # _ensure_remote_dir issues an mkdir-tree step and checks for a success marker; report
        # the tree as present. Every other submit (nobs integrity re-read) returns nobs_log.
        if "TROPIC_MKDIR" in code:
            return {"LOG": "TROPIC_MKDIR|/x|1\n"}
        return {"LOG": self.nobs_log}
    def endsas(self): self.ended = True


class FakeDownloadSas:
    def __init__(self, success=True, payload=b"payload", raise_exc=None):
        self.success, self.payload, self.raise_exc = success, payload, raise_exc
        self.downloads = []

    def download(self, local, remote, **kw):
        self.downloads.append((local, remote))
        if self.raise_exc:
            raise self.raise_exc
        if self.payload is not None:
            with open(local, "wb") as f:
                f.write(self.payload)
        return {"Success": self.success}


CONST_JITTER = lambda base, cap, n: 1.0
HEALTHY = lambda: "healthy"


class _FakeSeries:
    def __init__(self, values):
        self._values = values

    def tolist(self):
        return list(self._values)


class _FakeDf:
    def __init__(self, rows, names):
        self._rows = rows
        self._names = names

    def __len__(self):
        return len(self._rows)

    def __getitem__(self, name):
        idx = self._names.index(name)
        return _FakeSeries([row[idx] for row in self._rows])


class TestClassify(unittest.TestCase):
    def test_taxonomy(self):
        self.assertEqual(B.classify("invalid login: user/password"), "AUTH")
        self.assertEqual(B.classify("encryption key exchange failed"), "CONFIG_ENCRYPTION")
        self.assertEqual(B.classify("session limit reached: maximum"), "SESSION_LIMIT")
        self.assertEqual(B.classify("could not connect to any server in the cluster"), "CLUSTER_UNAVAILABLE")
        self.assertEqual(B.classify("SAS process has terminated unexpectedly"), "SPAWN_FAILED")
        self.assertEqual(B.classify("getaddrinfo failed"), "NETWORK")


class TestStatusPoller(unittest.TestCase):
    def test_statuspage_json_indicator_none_is_healthy(self):
        body = json.dumps({"status": {"indicator": "none"}})
        self.assertEqual(B._status_from_statuspage_json(body), "healthy")

    def test_statuspage_json_incident_indicators_are_unhealthy(self):
        for indicator in ("minor", "major", "critical"):
            body = json.dumps({"status": {"indicator": indicator}})
            self.assertEqual(B._status_from_statuspage_json(body), "unhealthy")

    def test_html_fallback_does_not_false_match_operational_components(self):
        html = "API operational; workspace server degraded; download page available"
        self.assertEqual(B._status_from_html(html), "unknown")

    def test_html_fallback_accepts_strong_healthy_phrase(self):
        self.assertEqual(B._status_from_html("All Systems Operational"), "healthy")


class TestDatasetJsonExporter(unittest.TestCase):
    def test_format_map_uses_pyreadstat_original_variable_types(self):
        meta = type("M", (), {"original_variable_types": {"ADT": "YYMMDD10", "AVAL": None}})()
        self.assertEqual(DJ._format_map(meta, ["ADT", "AVAL"]), {"ADT": "YYMMDD10", "AVAL": ""})

    def test_clean_cell_preserves_double_shape(self):
        self.assertIsInstance(DJ._clean_cell(1.0), float)
        self.assertEqual(DJ._clean_cell(1.0), 1.0)
        self.assertIsNone(DJ._clean_cell(float("nan")))

    def test_declared_key_sequence_must_exist(self):
        with self.assertRaisesRegex(RuntimeError, "missing variable"):
            DJ._derive_key_sequence("adcm", ["USUBJID", "CMDECOD"], DJ.ADAM_MDV)

    def test_sdtm_key_sequence_adds_seq_when_present(self):
        keyseq = DJ._derive_key_sequence("ae", ["STUDYID", "USUBJID", "AESEQ"], DJ.SDTM_MDV)
        self.assertEqual(keyseq, {"STUDYID": 1, "USUBJID": 2, "AESEQ": 3})

    def test_reconcile_output_reads_back_and_compares_source(self):
        td = tempfile.mkdtemp()
        path = os.path.join(td, "ae.json")
        doc = {
            "records": 2,
            "columns": [{"name": "USUBJID"}, {"name": "AVAL"}],
            "rows": [["01", 1.0], ["02", None]],
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(doc, f)
        meta = type("M", (), {"column_names": ["USUBJID", "AVAL"]})()
        df = _FakeDf([["01", 1.0], ["02", float("nan")]], ["USUBJID", "AVAL"])
        with mock.patch.object(DJ, "_read_xpt", return_value=(df, meta)):
            DJ._reconcile_output(path, "/fake/ae.xpt", ndjson=False)

    def test_reconcile_output_fails_on_stale_rows(self):
        td = tempfile.mkdtemp()
        path = os.path.join(td, "ae.ndjson")
        meta_line = {"records": 1, "columns": [{"name": "USUBJID"}]}
        with open(path, "w", encoding="utf-8") as f:
            f.write(json.dumps(meta_line) + "\n")
            f.write(json.dumps(["stale"]) + "\n")
        meta = type("M", (), {"column_names": ["USUBJID"]})()
        df = _FakeDf([["fresh"]], ["USUBJID"])
        with mock.patch.object(DJ, "_read_xpt", return_value=(df, meta)):
            with self.assertRaisesRegex(RuntimeError, "row values"):
                DJ._reconcile_output(path, "/fake/ae.xpt", ndjson=True)


class TestDatePrecisionSensitivity(unittest.TestCase):
    def test_tte_analysis_set_enforces_conditions_and_reports_exclusions(self):
        pd = __import__("pandas")
        df = pd.DataFrame({
            "PARAMCD": ["OS", "OS", "OS", "PFS"],
            "TRT01P": ["MP", "CBZP", "MP", "MP"],
            "AVAL": [10.0, 11.0, None, 12.0],
            "CNSR": [0.0, 0.0, 1.0, 1.0],
        })
        sub, counts = TU.tte_analysis_set(
            df,
            "OS",
            [{"variable": "TRT01P", "comparator": "EQ", "value": ["MP"]}],
        )
        self.assertEqual(len(sub), 1)
        self.assertEqual(counts.source_n, 2)
        self.assertEqual(counts.analyzed_n, 1)
        self.assertEqual(counts.excluded_missing, 1)
        self.assertEqual(counts.excluded_nonmatching, 1)

    def test_tte_analysis_set_rejects_missing_required_columns(self):
        pd = __import__("pandas")
        df = pd.DataFrame({"PARAMCD": ["OS"], "AVAL": [1.0], "CNSR": [0.0]})
        with self.assertRaisesRegex(ValueError, "TRT01P"):
            TU.tte_analysis_set(
                df,
                "OS",
                [{"variable": "TRT01P", "comparator": "EQ", "value": ["MP"]}],
            )

    def test_tte_analysis_set_rejects_invalid_censor_status(self):
        pd = __import__("pandas")
        df = pd.DataFrame({
            "PARAMCD": ["OS"], "TRT01P": ["MP"], "AVAL": [1.0], "CNSR": [2.0],
        })
        with self.assertRaisesRegex(ValueError, "invalid CNSR"):
            TU.tte_analysis_set(
                df,
                "OS",
                [{"variable": "TRT01P", "comparator": "EQ", "value": ["MP"]}],
            )

    def test_build_ars_records_condition_audit_counts(self):
        re_obj, ard_rows = ARS.build()
        first = re_obj["analyses"][0]
        self.assertIn("sourceRecordCount", first)
        self.assertIn("excludedRecordCounts", first)
        self.assertEqual(first["sourceRecordCount"], first["analyzedRecordCount"])
        self.assertIn("sourceRecordCount", ard_rows[0])


class TestUsdmBuilder(unittest.TestCase):
    def test_usdm_validator_catches_ct_code_decode_reuse(self):
        doc = {
            "instanceType": "Root",
            "id": "root",
            "codes": [
                {"instanceType": "Code", "id": "c1", "codeSystem": "ct", "code": "C1", "decode": "A"},
                {"instanceType": "Code", "id": "c2", "codeSystem": "ct", "code": "C1", "decode": "B"},
            ],
        }
        errors, _ = USDM.validate_usdm_dict(doc)
        self.assertTrue(any("multiple decodes" in e for e in errors))

    def test_usdm_validator_catches_unresolved_reference(self):
        doc = {
            "instanceType": "Root",
            "id": "root",
            "childId": "missing",
        }
        errors, _ = USDM.validate_usdm_dict(doc)
        self.assertTrue(any("unresolved reference" in e for e in errors))

    def test_usdm_objective_and_endpoint_ct_pairs_are_distinct(self):
        wrapper = USDM.build_wrapper()
        doc = json.loads(wrapper.model_dump_json(exclude_none=True))
        errors, _ = USDM.validate_usdm_dict(doc)
        self.assertEqual(errors, [])
        design = doc["study"]["versions"][0]["studyDesigns"][0]
        objective_pairs = {(o["level"]["code"], o["level"]["decode"]) for o in design["objectives"]}
        endpoint_pairs = {
            (e["level"]["code"], e["level"]["decode"])
            for o in design["objectives"] for e in o["endpoints"]
        }
        self.assertIn(("C85826", "Trial Primary Objective"), objective_pairs)
        self.assertIn(("C85827", "Trial Secondary Objective"), objective_pairs)
        self.assertIn(("C94496", "Primary Endpoint"), endpoint_pairs)
        self.assertIn(("C139173", "Secondary Endpoint"), endpoint_pairs)


class TestAdamDefineParser(unittest.TestCase):
    def _xml(self, text):
        path = os.path.join(tempfile.mkdtemp(), "define.xml")
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
        return path

    def test_parse_define_resolves_namespaced_structure_and_codelist(self):
        path = self._xml("""<?xml version="1.0"?>
<ODM xmlns:def="http://www.cdisc.org/ns/def/v2.1">
  <ItemDef OID="IT.ADSL.SEX" Name="SEX" DataType="text" Length="1">
    <Description><TranslatedText>Sex</TranslatedText></Description>
    <CodeListRef CodeListOID="CL.SEX"/>
  </ItemDef>
  <CodeList OID="CL.SEX"><CodeListItem CodedValue="M"/><CodeListItem CodedValue="F"/></CodeList>
  <ItemGroupDef Name="ADSL" def:Structure="One record per subject">
    <ItemRef ItemOID="IT.ADSL.SEX" Mandatory="Yes" OrderNumber="1"/>
  </ItemGroupDef>
</ODM>""")
        meta = ADEF.parse_define(path)
        self.assertEqual(meta["datasets"]["ADSL"]["structure"], "One record per subject")
        self.assertEqual(meta["datasets"]["ADSL"]["variables"][0]["label"], "Sex")
        self.assertEqual(meta["codelists"]["CL.SEX"]["values"], ["M", "F"])

    def test_parse_define_prefers_english_translated_text(self):
        path = self._xml("""<ODM>
  <ItemDef OID="IT.ADSL.SEX" Name="SEX" DataType="text">
    <Description><TranslatedText xml:lang="fr">Sexe</TranslatedText><TranslatedText xml:lang="en">Sex</TranslatedText></Description>
  </ItemDef>
  <ItemGroupDef Name="ADSL"><ItemRef ItemOID="IT.ADSL.SEX" OrderNumber="1"/></ItemGroupDef>
</ODM>""")
        meta = ADEF.parse_define(path)
        self.assertEqual(meta["datasets"]["ADSL"]["variables"][0]["label"], "Sex")

    def test_parse_define_marks_external_codelist(self):
        path = self._xml("""<ODM xmlns:def="http://www.cdisc.org/ns/def/v2.1" xmlns:xlink="http://www.w3.org/1999/xlink">
  <ItemDef OID="IT.ADAE.AEDECOD" Name="AEDECOD" DataType="text"><CodeListRef CodeListOID="CL.MEDDRA"/></ItemDef>
  <CodeList OID="CL.MEDDRA"><ExternalCodeList Dictionary="MedDRA" Version="27.0" xlink:href="meddra"/></CodeList>
  <ItemGroupDef Name="ADAE"><ItemRef ItemOID="IT.ADAE.AEDECOD" OrderNumber="1"/></ItemGroupDef>
</ODM>""")
        meta = ADEF.parse_define(path)
        self.assertTrue(meta["codelists"]["CL.MEDDRA"]["external"])
        self.assertEqual(meta["codelists"]["CL.MEDDRA"]["dictionary"], "MedDRA")

    def test_parse_define_resolves_vlm_items_and_where_clause(self):
        path = self._xml("""<ODM xmlns:def="http://www.cdisc.org/ns/def/v2.1">
  <def:ValueListDef OID="VL.ADEX.AVAL">
    <ItemRef ItemOID="IT.ADEX.AVAL.NCYCLE"><def:WhereClauseRef WhereClauseOID="WC.ADEX.PARAMCD.EQ.NCYCLE"/></ItemRef>
  </def:ValueListDef>
  <def:WhereClauseDef OID="WC.ADEX.PARAMCD.EQ.NCYCLE">
    <RangeCheck Comparator="EQ" def:ItemOID="IT.ADEX.PARAMCD"><CheckValue>NCYCLE</CheckValue></RangeCheck>
  </def:WhereClauseDef>
  <ItemDef OID="IT.ADEX.PARAMCD" Name="PARAMCD" DataType="text"/>
  <ItemDef OID="IT.ADEX.AVAL" Name="AVAL" DataType="float"><def:ValueListRef ValueListOID="VL.ADEX.AVAL"/></ItemDef>
  <ItemDef OID="IT.ADEX.AVAL.NCYCLE" Name="AVAL" DataType="integer"/>
  <ItemGroupDef Name="ADEX"><ItemRef ItemOID="IT.ADEX.PARAMCD" OrderNumber="1"/><ItemRef ItemOID="IT.ADEX.AVAL" OrderNumber="2"/></ItemGroupDef>
</ODM>""")
        meta = ADEF.parse_define(path)
        var = meta["datasets"]["ADEX"]["variables"][1]
        self.assertEqual(var["valuelist"], "VL.ADEX.AVAL")
        vl_item = meta["value_lists"]["VL.ADEX.AVAL"]["items"][0]
        self.assertEqual(vl_item["type"], "numeric")
        self.assertEqual(vl_item["where_clauses"][0][0]["variable"], "PARAMCD")
        self.assertEqual(vl_item["where_clauses"][0][0]["values"], ["NCYCLE"])

    def test_parse_define_fails_on_empty_metadata(self):
        path = self._xml("<ODM/>")
        with self.assertRaisesRegex(ValueError, "no datasets"):
            ADEF.parse_define(path)

    def test_parse_define_fails_on_unresolved_itemref(self):
        path = self._xml("""<ODM>
  <ItemGroupDef Name="ADSL"><ItemRef ItemOID="IT.MISSING" OrderNumber="1"/></ItemGroupDef>
</ODM>""")
        with self.assertRaisesRegex(ValueError, "missing ItemDef"):
            ADEF.parse_define(path)

    def test_parse_define_fails_on_missing_codelist(self):
        path = self._xml("""<ODM>
  <ItemDef OID="IT.ADSL.SEX" Name="SEX" DataType="text"><CodeListRef CodeListOID="CL.MISSING"/></ItemDef>
  <ItemGroupDef Name="ADSL"><ItemRef ItemOID="IT.ADSL.SEX" OrderNumber="1"/></ItemGroupDef>
</ODM>""")
        with self.assertRaisesRegex(ValueError, "missing CodeList"):
            ADEF.parse_define(path)


class TestGenerateConfig(unittest.TestCase):
    def _yaml(self, text):
        path = os.path.join(tempfile.mkdtemp(), "study_config.yaml")
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
        return path

    def test_yaml_quotes_preserve_hash_and_strings_are_macro_quoted(self):
        cfg = GC.parse_yaml(self._yaml(
            'STUDY_TITLE: "Trial #6193 Extension"\n'
            'STAGING_PATH: "01_raw_source/real_sdtm/staging"\n'
            'STUDY_CUTOFF_DT: "2009-09-25"\n'
        ))
        text = GC.render_sas_config(cfg)
        self.assertIn("%let STUDY_TITLE = %nrstr(Trial #6193 Extension);", text)
        self.assertIn("%let STAGING_PATH = %nrstr(01_raw_source/real_sdtm/staging);", text)
        self.assertIn("%let STUDY_CUTOFF_DT = '25SEP2009'd;", text)

    def test_rejects_sas_statement_terminator_in_string_value(self):
        cfg = GC.parse_yaml(self._yaml('BAD: "ok; %put hacked"\n'))
        with self.assertRaisesRegex(GC.ConfigError, "semicolons"):
            GC.render_sas_config(cfg)

    def test_rejects_nested_yaml_values(self):
        with self.assertRaisesRegex(GC.ConfigError, "nested/list"):
            GC.parse_yaml(self._yaml("BAD:\n  - a\n  - b\n"))

    def test_bad_cutoff_date_has_specific_error(self):
        cfg = GC.parse_yaml(self._yaml("STUDY_CUTOFF_DT: 20090925\n"))
        with self.assertRaisesRegex(GC.ConfigError, "YYYY-MM-DD"):
            GC.render_sas_config(cfg)

    def test_generate_is_content_stable_when_output_matches(self):
        cfg = {"STUDYID": "TROPIC"}
        rendered = GC.render_sas_config(cfg)
        writes = []
        changed = GC.generate_sas_config(
            cfg, "/tmp/00_config_generated.sas",
            exists_fn=lambda p: True,
            read_fn=lambda p: rendered,
            write_fn=lambda p, content: writes.append((p, content)))
        self.assertFalse(changed)
        self.assertEqual(writes, [])


class TestCtCrossValidation(unittest.TestCase):
    def _ct_indices(self):
        codelists = [
            {
                "conceptId": "CNY", "name": "No Yes Response", "extensible": False,
                "terms": [
                    {"submissionValue": "Y", "preferredTerm": "Yes"},
                    {"submissionValue": "N", "preferredTerm": "No"},
                ],
            },
            {
                "conceptId": "CSEV", "name": "Severity", "extensible": False,
                "terms": [
                    {"submissionValue": "MILD", "preferredTerm": "Mild"},
                    {"submissionValue": "MODERATE", "preferredTerm": "Moderate"},
                    {"submissionValue": "SEVERE", "preferredTerm": "Severe"},
                ],
            },
        ]
        return CTV.index_ct(codelists)

    def test_name_link_is_medium_and_does_not_hard_violate(self):
        by_ccode, by_name, value_sets = self._ct_indices()
        spec = {"CL.SEV": {"id": "CL.SEV", "name": "Severity", "nci_ccode": None,
                           "terms": [{"value": "MILD", "decode": "Mild"},
                                     {"value": "BAD", "decode": "Bad"}]}}
        results, summary = CTV.validate(spec, by_ccode, by_name, value_sets)
        self.assertEqual(results[0]["link_confidence"], "medium")
        self.assertEqual(results[0]["status"], "review")
        self.assertEqual(summary["violations"], 0)

    def test_numeric_only_values_are_not_sponsor_defined(self):
        by_ccode, by_name, value_sets = self._ct_indices()
        spec = {"CL.NUM": {"id": "CL.NUM", "name": "Numeric Codes", "nci_ccode": None,
                           "terms": [{"value": "1", "decode": "One"},
                                     {"value": "2", "decode": "Two"}]}}
        results, summary = CTV.validate(spec, by_ccode, by_name, value_sets)
        self.assertEqual(results[0]["classification"], "unverifiable-numeric")
        self.assertEqual(summary["sponsor_defined"], 0)
        self.assertEqual(summary["unverifiable_numeric"], 1)

    def test_near_miss_is_possible_cdisc_mismatch(self):
        by_ccode, by_name, value_sets = self._ct_indices()
        spec = {"CL.NY": {"id": "CL.NY", "name": "Custom", "nci_ccode": None,
                          "terms": [{"value": "Y", "decode": "Yes"},
                                    {"value": "NOPE", "decode": "Nope"}]}}
        results, summary = CTV.validate(spec, by_ccode, by_name, value_sets)
        self.assertEqual(results[0]["classification"], "possible-cdisc-mismatch")
        self.assertEqual(summary["possible_cdisc_mismatch"], 1)
        self.assertEqual(summary["traceability_gaps"], 1)

    def test_missing_decode_is_separate_from_decode_mismatch(self):
        by_ccode, by_name, value_sets = self._ct_indices()
        spec = {"CL.NY": {"id": "CL.NY", "name": "No Yes", "nci_ccode": "CNY",
                          "terms": [{"value": "Y", "decode": None},
                                    {"value": "N", "decode": "Wrong"}]}}
        results, _ = CTV.validate(spec, by_ccode, by_name, value_sets)
        self.assertEqual(results[0]["missing_decodes"], ["Y"])
        self.assertEqual(results[0]["decode_mismatches"], ["N"])


class TestFailoverStatus(unittest.TestCase):
    def _cfg(self, text):
        path = os.path.join(tempfile.mkdtemp(), "sascfg_personal.py")
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
        return path

    def test_single_host_reports_missing_regional_failover_hosts(self):
        cfg = self._cfg("oda = {'iomhost': 'odaws01-apse1.oda.sas.com'}\n")
        status = B.failover_status(cfg)
        self.assertEqual(status["oda_region"], "apse1")
        self.assertFalse(status["oda_failover_configured"])
        self.assertEqual(status["oda_configured_hosts"], ["odaws01-apse1.oda.sas.com"])
        self.assertEqual(status["oda_missing_failover_hosts"], ["odaws02-apse1.oda.sas.com"])

    def test_full_host_list_reports_failover_configured(self):
        cfg = self._cfg(
            "oda = {'iomhost': ['odaws01-apse1.oda.sas.com', 'odaws02-apse1.oda.sas.com']}\n"
        )
        status = B.failover_status(cfg)
        self.assertEqual(status["oda_region"], "apse1")
        self.assertTrue(status["oda_failover_configured"])
        self.assertEqual(status["oda_missing_failover_hosts"], [])

    def test_short_hosts_are_normalized(self):
        cfg = self._cfg("oda = {'iomhost': ['odaws01-euw1', 'odaws02-euw1']}\n")
        status = B.failover_status(cfg)
        self.assertTrue(status["oda_failover_configured"])
        self.assertEqual(status["oda_configured_hosts"],
                         ["odaws01-euw1.oda.sas.com", "odaws02-euw1.oda.sas.com"])


class TestPreflight(unittest.TestCase):
    def _cfg(self, text):
        path = os.path.join(tempfile.mkdtemp(), "sascfg_personal.py")
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
        return path

    def test_preflight_ok_is_credential_safe(self):
        cfg = self._cfg(
            "oda = {'java': 'java', 'iomhost': ['odaws01-apse1-2.oda.sas.com', "
            "'odaws02-apse1-2.oda.sas.com'], 'iomport': 8591, 'authkey': 'oda'}\n"
        )
        stat_obj = type("S", (), {"st_mode": 0o100600})()
        run_obj = type("R", (), {"stderr": 'openjdk version "26.0.1"', "stdout": ""})()
        saspy_mod = type("Saspy", (), {"__version__": "test"})()
        status = B.preflight(
            cfg_file=cfg, authinfo_path="/tmp/.authinfo", which_fn=lambda x: "/bin/java",
            exists_fn=lambda p: True, stat_fn=lambda p: stat_obj, run_fn=lambda *a, **k: run_obj,
            saspy_importer=lambda: saspy_mod)
        self.assertTrue(status["oda_preflight_ok"])
        self.assertEqual(status["oda_preflight_missing"], [])
        self.assertTrue(status["oda_failover_configured"])
        self.assertNotIn("password", json.dumps(status).lower())

    def test_preflight_reports_missing_required_local_prereqs(self):
        cfg = self._cfg("oda = {'iomhost': 'odaws01-apse1.oda.sas.com'}\n")
        status = B.preflight(
            cfg_file=cfg, authinfo_path="/tmp/missing", which_fn=lambda x: None,
            exists_fn=lambda p: False,
            stat_fn=lambda p: (_ for _ in ()).throw(OSError("missing")),
            run_fn=lambda *a, **k: None,
            saspy_importer=lambda: (_ for _ in ()).throw(ImportError("no saspy")))
        self.assertFalse(status["oda_preflight_ok"])
        for key in ("java", "saspy", "authkey", "authinfo", "authinfo_mode_600"):
            self.assertIn(key, status["oda_preflight_missing"])
        self.assertFalse(status["oda_failover_configured"])


class TestBroker(unittest.TestCase):
    def setUp(self):
        # Isolate broker side-effects (breadcrumb/ledger) to a temp dir per test so a
        # live session's breadcrumb can't leak an orphan-sweep cooldown into the next test.
        self._td = tempfile.mkdtemp()
        self._orig = (B.BREADCRUMB, B.LEDGER, B.LOCKFILE)
        B.BREADCRUMB = os.path.join(self._td, "crumb.json")
        B.LEDGER = os.path.join(self._td, "ledger.json")
        B.LOCKFILE = os.path.join(self._td, "lock")

    def tearDown(self):
        B.BREADCRUMB, B.LEDGER, B.LOCKFILE = self._orig

    def test_probe_failure_never_yields_oda(self):
        """A connected-but-dead workspace (probe fails) must NOT return a session; mode falls to
        sim (caller catches OdaExhausted). Teardown must run on the dead session."""
        sas = FakeSas()
        clk = FakeClock()
        with self.assertRaises(B.OdaExhausted):
            B.connect(max_wait_s=3, lock=False, jitter=CONST_JITTER,
                      clock=clk.read, sleep_fn=clk.sleep, status_poller=HEALTHY,
                      session_factory=lambda t: (sas, "odaws01-apse1.oda.sas.com"),
                      prober=lambda s, n: False)
        self.assertTrue(sas.ended, "teardown() must be called on the failed-spawn session")

    def test_live_probe_earns_oda(self):
        sas = FakeSas()
        clk = FakeClock()
        conn = B.connect(max_wait_s=10, lock=False, jitter=CONST_JITTER,
                         clock=clk.read, sleep_fn=clk.sleep, status_poller=HEALTHY,
                         session_factory=lambda t: (sas, "odaws03-usw2.oda.sas.com"),
                         prober=lambda s, n: True)
        self.assertIs(conn.sas, sas)
        self.assertEqual(conn.endpoint, "odaws03-usw2.oda.sas.com")
        self.assertTrue(conn.probe_nonce_echoed)
        self.assertGreaterEqual(conn.attempts, 1)
        B.teardown(conn.sas)  # caller owns the live session; tear it down

    def test_connection_context_manager_tears_down(self):
        sas = FakeSas()
        clk = FakeClock()
        with B.connect(max_wait_s=10, lock=False, jitter=CONST_JITTER,
                       clock=clk.read, sleep_fn=clk.sleep, status_poller=HEALTHY,
                       session_factory=lambda t: (sas, "odaws03-usw2.oda.sas.com"),
                       prober=lambda s, n: True) as conn:
            self.assertIs(conn.sas, sas)
        self.assertTrue(sas.ended)

    def test_auth_fails_fast_without_consuming_budget(self):
        calls = {"n": 0}
        def factory(t):
            calls["n"] += 1
            raise RuntimeError("ERROR: Invalid login: user/password could not be authenticated")
        clk = FakeClock()
        with self.assertRaises(B.OdaFatal) as ctx:
            B.connect(max_wait_s=3600, lock=False, jitter=CONST_JITTER,
                      clock=clk.read, sleep_fn=clk.sleep, status_poller=HEALTHY,
                      session_factory=factory, prober=lambda s, n: True)
        self.assertEqual(ctx.exception.error_class, "AUTH")
        self.assertEqual(calls["n"], 1, "AUTH must abort on first attempt, not loop")

    def test_backoff_is_jittered_not_blind(self):
        """Transient failures retry via injected jitter (no fixed sleep); budget is the bound."""
        sleeps = []
        clk = FakeClock()
        def rec_sleep(d): sleeps.append(d); clk.sleep(d)
        with self.assertRaises(B.OdaExhausted):
            B.connect(max_wait_s=3, lock=False, jitter=CONST_JITTER,
                      clock=clk.read, sleep_fn=rec_sleep, status_poller=HEALTHY,
                      session_factory=lambda t: (_ for _ in ()).throw(
                          RuntimeError("SAS process has terminated unexpectedly")),
                      prober=lambda s, n: True)
        self.assertTrue(sleeps, "must back off between attempts")
        # SPAWN_FAILED carries a cooldown; every sleep is bounded and non-negative.
        self.assertTrue(all(s >= 0 for s in sleeps))

    def test_jittered_bounds_vary_and_cap(self):
        vals = [B._jittered(base=5, cap=120, n=3) for _ in range(40)]
        self.assertTrue(all(0 <= v <= 40 for v in vals))
        self.assertGreater(len({round(v, 6) for v in vals}), 1)
        self.assertLessEqual(B._jittered(base=5, cap=120, n=20), 120)

    def test_retry_sleep_is_capped_to_remaining_budget(self):
        sleeps = []
        clk = FakeClock()
        def rec_sleep(d): sleeps.append(d); clk.sleep(d)
        with self.assertRaises(B.OdaExhausted):
            B.connect(max_wait_s=3, lock=False, jitter=lambda base, cap, n: 100.0,
                      clock=clk.read, sleep_fn=rec_sleep, status_poller=HEALTHY,
                      session_factory=lambda t: (_ for _ in ()).throw(
                          RuntimeError("SAS process has terminated unexpectedly")),
                      prober=lambda s, n: True)
        self.assertLessEqual(clk.read(), 3)
        self.assertEqual(sleeps, [3])

    def test_orphan_cooldown_is_capped_to_remaining_budget(self):
        clk = FakeClock()
        sleeps = []
        with open(B.BREADCRUMB, "w", encoding="utf-8") as f:
            json.dump({"pid": 1, "endpoint": "stale"}, f)
        with self.assertRaises(B.OdaExhausted) as ctx:
            B.connect(max_wait_s=10, lock=False, jitter=CONST_JITTER,
                      clock=clk.read,
                      sleep_fn=lambda d: (sleeps.append(d), clk.sleep(d)),
                      status_poller=HEALTHY,
                      session_factory=lambda t: (_ for _ in ()).throw(
                          AssertionError("must not spawn after orphan cooldown consumes budget")),
                      prober=lambda s, n: True)
        self.assertEqual(ctx.exception.last_class, "ORPHAN_SWEEP")
        self.assertEqual(sleeps, [10])

    def test_orphan_cooldown_uses_named_constant(self):
        old = B.ORPHAN_SWEEP_COOLDOWN
        try:
            B.ORPHAN_SWEEP_COOLDOWN = 7
            clk = FakeClock()
            sleeps = []
            with open(B.BREADCRUMB, "w", encoding="utf-8") as f:
                json.dump({"pid": 1, "endpoint": "stale"}, f)
            with self.assertRaises(B.OdaExhausted):
                B.connect(max_wait_s=7, lock=False, jitter=CONST_JITTER,
                          clock=clk.read,
                          sleep_fn=lambda d: (sleeps.append(d), clk.sleep(d)),
                          status_poller=HEALTHY,
                          session_factory=lambda t: (_ for _ in ()).throw(
                              AssertionError("budget consumed by orphan cooldown")),
                          prober=lambda s, n: True)
            self.assertEqual(sleeps, [7])
        finally:
            B.ORPHAN_SWEEP_COOLDOWN = old

    def test_recommend_window(self):
        led = os.path.join(tempfile.mkdtemp(), "ledger.json")
        self.assertIsNone(B.recommend_window(led))
        with open(led, "w") as f:
            for h in (14, 14, 15):
                f.write(json.dumps({"ts": f"2026-06-12T{h:02d}:30:00+05:30",
                                    "error_class": None}) + "\n")
        win = B.recommend_window(led)
        self.assertIsNotNone(win)
        self.assertRegex(win, r"\d{2}:00-\d{2}:00")

    def test_recommend_window_needs_multiple_successes(self):
        led = os.path.join(tempfile.mkdtemp(), "ledger.json")
        with open(led, "w") as f:
            f.write(json.dumps({"ts": "2026-06-12T14:30:00+05:30",
                                "error_class": None}) + "\n")
        self.assertIsNone(B.recommend_window(led))


class TestProber(unittest.TestCase):
    """Regression: the live probe must read the RESOLVED %put output, not assert that
    '&sysjobid' is absent. ODA echoes the SOURCE line (which contains the literal
    '&sysjobid.') by default, which previously failed every live session as SPAWN_FAILED."""
    NONCE = "12345-9999999"

    def _sas(self, log):
        return type("S", (), {"submit": lambda self, code, _log=log: {"LOG": _log}})()

    def test_resolved_output_with_echoed_source_passes(self):
        # Real ODA log: line 26 echoes the source (literal &sysjobid.), then the resolved output.
        n = self.NONCE
        log = (f"26   %put ODA_LIVE=&sysjobid.|{n}|&sysscp.;\n"
               f"ODA_LIVE=97614|{n}|LIN X64\n")
        self.assertTrue(B._default_prober(self._sas(log), n))

    def test_stale_log_without_nonce_fails(self):
        log = "ODA_LIVE=97614|some-OTHER-nonce|LIN X64\n"
        self.assertFalse(B._default_prober(self._sas(log), self.NONCE))

    def test_unresolved_macro_fails(self):
        # Workspace not really live: macro never resolved, only the echoed source carries the nonce.
        n = self.NONCE
        log = (f"26   %put ODA_LIVE=&sysjobid.|{n}|&sysscp.;\n"
               "WARNING: Apparent symbolic reference SYSJOBID not resolved.\n")
        self.assertFalse(B._default_prober(self._sas(log), n))

    def test_submit_exception_fails(self):
        sas = type("S", (), {"submit": lambda self, code: (_ for _ in ()).throw(RuntimeError("dead"))})()
        self.assertFalse(B._default_prober(sas, self.NONCE))


class TestSeedIdempotent(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        for name, data in (("dm.sas7bdat", b"AAAA"), ("ae.sas7bdat", b"BBBBBB")):
            with open(os.path.join(self.d, name), "wb") as f:
                f.write(data)
        self.local = S.compute_local_manifest(self.d)
        self.local["datasets"]["dm.sas7bdat"]["nrows"] = 4
        self.local["datasets"]["ae.sas7bdat"]["nrows"] = 6
        self.nobs_log = "SEEDNOBS|DM|4\nSEEDNOBS|AE|6\n"

    def test_manifest_match_skips_upload(self):
        sas = FakeSas(remote_manifest=self.local)  # ODA already has exactly this source
        res = S.seed(sas, sdtm_dir=self.d, remote_dir="/x", force=False)
        self.assertEqual(res["status"], "already-resident")
        self.assertEqual(res["uploaded"], 0)
        self.assertEqual(sas.uploaded, [], "must perform ZERO uploads when manifest matches")

    def test_missing_remote_manifest_triggers_seed(self):
        sas = FakeSas(remote_manifest=None, nobs_log=self.nobs_log)  # nothing on ODA -> not resident
        ok, _, reason = S.verify_resident(sas, sdtm_dir=self.d, remote_dir="/x", local=self.local)
        self.assertFalse(ok)
        old_compute = S.compute_local_manifest
        try:
            S.compute_local_manifest = lambda sdtm_dir=self.d: self.local
            res = S.seed(sas, sdtm_dir=self.d, remote_dir="/x", force=False)
        finally:
            S.compute_local_manifest = old_compute
        self.assertEqual(res["status"], "seeded")
        # uploaded the 2 data files + the manifest sentinel (written LAST)
        self.assertIn(S.MANIFEST_NAME, sas.uploaded)
        self.assertEqual(sas.uploaded[-1], S.MANIFEST_NAME, "manifest must be uploaded LAST")

    def test_changed_source_fails_match(self):
        stale = json.loads(json.dumps(self.local))
        stale["datasets"]["dm.sas7bdat"]["sha256"] = "deadbeef"
        self.assertFalse(S.manifests_match(self.local, stale))

    def test_force_overrides_resident(self):
        sas = FakeSas(remote_manifest=self.local, nobs_log=self.nobs_log)
        old_compute = S.compute_local_manifest
        try:
            S.compute_local_manifest = lambda sdtm_dir=self.d: self.local
            res = S.seed(sas, sdtm_dir=self.d, remote_dir="/x", force=True)
        finally:
            S.compute_local_manifest = old_compute
        self.assertEqual(res["status"], "seeded")
        self.assertGreater(len(sas.uploaded), 0)

    def test_stale_members_selects_only_changed(self):
        # Pure diff: a single changed member; absent/forced manifest -> the whole library.
        remote = json.loads(json.dumps(self.local))
        remote["datasets"]["dm.sas7bdat"]["sha256"] = "changed"
        self.assertEqual(S.stale_members(self.local, remote), ["dm.sas7bdat"])
        self.assertEqual(S.stale_members(self.local, None), ["ae.sas7bdat", "dm.sas7bdat"])
        self.assertEqual(S.stale_members(self.local, self.local, force=True),
                         ["ae.sas7bdat", "dm.sas7bdat"])

    def test_partial_change_uploads_only_delta(self):
        # ODA has a matching dm but a STALE ae -> only ae (+ the manifest) must upload; the
        # ~200 MB cost should track the delta, not the whole library.
        remote = json.loads(json.dumps(self.local))
        remote["datasets"]["ae.sas7bdat"]["sha256"] = "stale-ae-hash"
        sas = FakeSas(remote_manifest=remote, nobs_log=self.nobs_log)
        old_compute = S.compute_local_manifest
        try:
            S.compute_local_manifest = lambda sdtm_dir=self.d: self.local
            res = S.seed(sas, sdtm_dir=self.d, remote_dir="/x", force=False)
        finally:
            S.compute_local_manifest = old_compute
        self.assertEqual(res["status"], "seeded")
        self.assertEqual((res["uploaded"], res["skipped"]), (1, 1))
        self.assertIn("ae.sas7bdat", sas.uploaded)
        self.assertNotIn("dm.sas7bdat", sas.uploaded)       # unchanged member NOT re-uploaded
        self.assertEqual(sas.uploaded[-1], S.MANIFEST_NAME)  # manifest still written LAST

    def test_uppercase_local_names_match_sas_uppercase_memnames(self):
        d = tempfile.mkdtemp()
        for name, data in (("DM.sas7bdat", b"AAAA"), ("AE.sas7bdat", b"BBBBBB")):
            with open(os.path.join(d, name), "wb") as f:
                f.write(data)
        local = S.compute_local_manifest(d)
        local["datasets"]["DM.sas7bdat"]["nrows"] = 4
        local["datasets"]["AE.sas7bdat"]["nrows"] = 6
        sas = FakeSas(remote_manifest=None, nobs_log="SEEDNOBS|DM|4\nSEEDNOBS|AE|6\n")
        old_compute = S.compute_local_manifest
        try:
            S.compute_local_manifest = lambda sdtm_dir=d: local
            res = S.seed(sas, sdtm_dir=d, remote_dir="/x", force=False)
        finally:
            S.compute_local_manifest = old_compute
        self.assertEqual(res["status"], "seeded")
        self.assertEqual(sas.uploaded[-1], S.MANIFEST_NAME)

    def test_uppercase_local_names_fail_on_wrong_remote_count(self):
        d = tempfile.mkdtemp()
        for name, data in (("DM.sas7bdat", b"AAAA"), ("AE.sas7bdat", b"BBBBBB")):
            with open(os.path.join(d, name), "wb") as f:
                f.write(data)
        local = S.compute_local_manifest(d)
        local["datasets"]["DM.sas7bdat"]["nrows"] = 4
        local["datasets"]["AE.sas7bdat"]["nrows"] = 6
        sas = FakeSas(remote_manifest=None, nobs_log="SEEDNOBS|DM|99\nSEEDNOBS|AE|6\n")
        old_compute = S.compute_local_manifest
        try:
            S.compute_local_manifest = lambda sdtm_dir=d: local
            res = S.seed(sas, sdtm_dir=d, remote_dir="/x", force=False)
        finally:
            S.compute_local_manifest = old_compute
        self.assertEqual(res["status"], "VERIFY_FAILED")
        self.assertIn("DM.sas7bdat: local 4 != ODA 99", "\n".join(res["mismatches"]))
        self.assertNotEqual(sas.uploaded[-1], S.MANIFEST_NAME)

    def test_verify_remote_nobs_direct_case_normalized(self):
        local = {"datasets": {"AE.sas7bdat": {"nrows": 6}, "DM.sas7bdat": {"nrows": 4}}}
        self.assertEqual(S.verify_remote_nobs(local, {"ae.sas7bdat": 6, "dm.sas7bdat": 4}), [])
        self.assertEqual(S.verify_remote_nobs(local, {"ae.sas7bdat": 5, "dm.sas7bdat": 4}),
                         ["AE.sas7bdat: local 6 != ODA 5"])

    def test_missing_remote_member_fails_verify(self):
        sas = FakeSas(remote_manifest=None, nobs_log="SEEDNOBS|DM|4\n")
        old_compute = S.compute_local_manifest
        try:
            S.compute_local_manifest = lambda sdtm_dir=self.d: self.local
            res = S.seed(sas, sdtm_dir=self.d, remote_dir="/x", force=False)
        finally:
            S.compute_local_manifest = old_compute
        self.assertEqual(res["status"], "VERIFY_FAILED")
        self.assertIn("ae.sas7bdat: missing", "\n".join(res["mismatches"]))
        self.assertNotEqual(sas.uploaded[-1], S.MANIFEST_NAME)

    def test_no_local_row_counts_fails_closed(self):
        local = json.loads(json.dumps(self.local))
        for d in local["datasets"].values():
            d["nrows"] = None
        sas = FakeSas(remote_manifest=None, nobs_log=self.nobs_log)
        old_compute = S.compute_local_manifest
        try:
            S.compute_local_manifest = lambda sdtm_dir=self.d: local
            res = S.seed(sas, sdtm_dir=self.d, remote_dir="/x", force=False)
        finally:
            S.compute_local_manifest = old_compute
        self.assertEqual(res["status"], "VERIFY_FAILED")
        self.assertIn("VERIFY_SKIPPED", res["mismatches"][0])
        self.assertNotEqual(sas.uploaded[-1], S.MANIFEST_NAME)


class TestOdaRenderTflHelpers(unittest.TestCase):
    def setUp(self):
        import _oda_render_tfl as R
        self.R = R

    def test_import_is_side_effect_free(self):
        with mock.patch("oda_broker.connect") as connect:
            import importlib
            import _oda_render_tfl as R
            importlib.reload(R)
            connect.assert_not_called()

    def test_errors_in_detects_sas_error_signatures(self):
        log = "\n".join([
            "NOTE: harmless",
            "ERROR 22-322: Syntax error",
            "  _ERROR_=1 _N_=3",
            "NOTE: The SAS System stopped processing this step because of errors.",
        ])
        errs = self.R.errors_in(log)
        self.assertEqual(len(errs), 3)

    def test_download_checked_uses_part_file_and_replaces(self):
        td = tempfile.mkdtemp()
        local = os.path.join(td, "out.png")
        with open(local, "wb") as f:
            f.write(b"stale")
        sas = FakeDownloadSas(payload=b"fresh")
        ok, msg = self.R._download_checked(sas, local, "/remote/out.png", "out.png")
        self.assertTrue(ok, msg)
        with open(local, "rb") as f:
            self.assertEqual(f.read(), b"fresh")
        self.assertFalse(os.path.exists(local + ".part"))

    def test_download_checked_fails_closed_and_removes_stale_local(self):
        td = tempfile.mkdtemp()
        local = os.path.join(td, "out.png")
        with open(local, "wb") as f:
            f.write(b"stale")
        sas = FakeDownloadSas(success=False, payload=None)
        ok, msg = self.R._download_checked(sas, local, "/remote/out.png", "out.png")
        self.assertFalse(ok)
        self.assertIn("download failed", msg)
        self.assertFalse(os.path.exists(local))
        self.assertFalse(os.path.exists(local + ".part"))

    def test_purge_remote_outputs_requires_marker(self):
        calls = []
        sas = type("S", (), {"submit": lambda self, code: (calls.append(code), {"LOG": ""})[1]})()
        with self.assertRaises(SystemExit):
            self.R._purge_remote_outputs(sas)
        self.assertIn("fdelete", calls[0])
        self.assertIn("TROPIC_PURGE_TFL|DONE", calls[0])

    def test_purge_remote_outputs_accepts_marker(self):
        sas = type("S", (), {"submit": lambda self, code: {"LOG": "TROPIC_PURGE_TFL|DONE"}})()
        self.R._purge_remote_outputs(sas)


class _FakeKillSas:
    """Session whose local child pid and endsas() are controllable for teardown tests."""
    def __init__(self, child_pid=None):
        self.ended = False
        if child_pid is not None:
            # mimic saspy IOM: sas._io.pid is a Popen whose .pid is the OS pid
            self._io = type("IO", (), {"pid": type("P", (), {"pid": child_pid})()})()
    def endsas(self):
        self.ended = True


def _kill_recorder():
    calls = []
    return calls, (lambda pid, sig: calls.append((pid, sig)))


# call_with_timeout stub that RUNS fn and reports completion (the normal, non-hung path)
_RAN = lambda fn, t: (fn(), True)[1]


class TestTeardownForceKill(unittest.TestCase):
    """Finding 2: teardown must force-kill the lingering local Java/SAS child so a wedged
    endsas() can't leave a CPU-burning zombie. The server-side ODA slot is ODA's to reap."""
    def setUp(self):
        self._td = tempfile.mkdtemp()
        self._orig = B.BREADCRUMB
        B.BREADCRUMB = os.path.join(self._td, "crumb.json")

    def tearDown(self):
        B.BREADCRUMB = self._orig

    def test_kills_alive_child_after_graceful_endsas(self):
        sas = _FakeKillSas(child_pid=4242)
        calls, kill = _kill_recorder()
        B.teardown(sas, kill_fn=kill, alive_fn=lambda pid: True, call_with_timeout=_RAN)
        self.assertTrue(sas.ended, "graceful endsas() must still be attempted")
        self.assertEqual(calls, [(4242, signal.SIGKILL)])

    def test_no_kill_when_child_already_dead(self):
        sas = _FakeKillSas(child_pid=4242)
        calls, kill = _kill_recorder()
        B.teardown(sas, kill_fn=kill, alive_fn=lambda pid: False, call_with_timeout=_RAN)
        self.assertTrue(sas.ended)
        self.assertEqual(calls, [], "a cleanly-ended session must not be SIGKILLed")

    def test_force_skips_endsas_but_kills(self):
        """force=True (post exec-timeout): a worker thread may still be blocked in submit() on
        this session, so endsas() must be SKIPPED (it would race that thread) and we kill."""
        sas = _FakeKillSas(child_pid=99)
        calls, kill = _kill_recorder()
        boom = lambda fn, t: (_ for _ in ()).throw(AssertionError("endsas must not run on force"))
        B.teardown(sas, force=True, kill_fn=kill, alive_fn=lambda pid: True, call_with_timeout=boom)
        self.assertFalse(sas.ended)
        self.assertEqual(calls, [(99, signal.SIGKILL)])

    def test_no_child_pid_no_kill(self):
        sas = _FakeKillSas(child_pid=None)  # no _io -> pid undiscoverable
        calls, kill = _kill_recorder()
        B.teardown(sas, kill_fn=kill, alive_fn=lambda pid: True, call_with_timeout=_RAN)
        self.assertTrue(sas.ended)
        self.assertEqual(calls, [])

    def test_none_session_is_safe(self):
        calls, kill = _kill_recorder()
        B.teardown(None, kill_fn=kill, alive_fn=lambda pid: True, call_with_timeout=_RAN)
        self.assertEqual(calls, [])  # nothing to end or kill; must not raise


class TestSessionChildPid(unittest.TestCase):
    def test_popen_like(self):
        self.assertEqual(B._session_child_pid(_FakeKillSas(child_pid=777)), 777)

    def test_bare_int_pid(self):
        sas = type("S", (), {"_io": type("IO", (), {"pid": 555})()})()
        self.assertEqual(B._session_child_pid(sas), 555)

    def test_none_when_no_io_or_reaped(self):
        self.assertIsNone(B._session_child_pid(object()))
        self.assertIsNone(B._session_child_pid(None))
        reaped = type("S", (), {"_io": type("IO", (), {"pid": None})()})()
        self.assertIsNone(B._session_child_pid(reaped))


class TestCallWithTimeout(unittest.TestCase):
    def test_quick_fn_completes(self):
        ran = []
        self.assertTrue(B._call_with_timeout(lambda: ran.append(1), 2.0))
        self.assertEqual(ran, [1])

    def test_hung_fn_times_out(self):
        block = threading.Event()
        try:
            self.assertFalse(B._call_with_timeout(lambda: block.wait(30), 0.15))
        finally:
            block.set()  # release the daemon worker


class TestSubmitTimed(unittest.TestCase):
    """Finding 3: a wedged server-side workspace must not block submit() forever."""
    def test_returns_result_on_quick_submit(self):
        sas = type("S", (), {"submit": lambda self, code: {"LOG": "ok"}})()
        self.assertEqual(B.submit_timed(sas, "x", timeout_s=2)["LOG"], "ok")

    def test_raises_exec_timeout_on_hang(self):
        block = threading.Event()
        sas = type("S", (), {"submit": lambda self, code: block.wait(30)})()
        try:
            with self.assertRaises(B.OdaExecTimeout):
                B.submit_timed(sas, "x", timeout_s=0.15)
        finally:
            block.set()

    def test_propagates_submit_exception_unchanged(self):
        sas = type("S", (), {"submit": lambda self, code:
                             (_ for _ in ()).throw(RuntimeError("boom"))})()
        with self.assertRaises(RuntimeError):
            B.submit_timed(sas, "x", timeout_s=2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
