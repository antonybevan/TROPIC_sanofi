#!/usr/bin/env python3
"""Build aggregate source-data profiling evidence for the TROPIC SDTM release.

The report is intentionally aggregate-only: it records domain sizes, variable
availability, missingness percentages, duplicate-key counts, and timing-variable
patterns without printing subject-level records or patient values.
"""

import argparse
import csv
import glob
import json
import os
import sys
from datetime import datetime, timezone

import pandas as pd
import pyreadstat


EXPECTED_VARIABLES = {
    "dm": ["STUDYID", "DOMAIN", "USUBJID", "SUBJID", "RFSTDTC", "RFENDTC", "AGEU", "SEX", "RACE", "ARM", "ARMCD"],
    "ex": ["STUDYID", "DOMAIN", "USUBJID", "EXSEQ", "EXTRT", "EXSTDTC", "EXENDTC", "EXDOSE", "EXDOSU"],
    "ds": ["STUDYID", "DOMAIN", "USUBJID", "DSSEQ", "DSTERM", "DSDECOD", "DSCAT", "DSSTWK"],
    "ae": ["STUDYID", "DOMAIN", "USUBJID", "AESEQ", "AETERM", "AEDECOD", "AEBODSYS", "AESER", "AEREL"],
    "lb": ["STUDYID", "DOMAIN", "USUBJID", "LBSEQ", "LBTESTCD", "LBTEST", "LBSTRESN", "LBSTRESU", "LBDTC"],
    "vs": ["STUDYID", "DOMAIN", "USUBJID", "VSSEQ", "VSTESTCD", "VSTEST", "VSSTRESN", "VSSTRESU", "VSDTC"],
    "ls": ["STUDYID", "DOMAIN", "USUBJID"],
    "pn": ["STUDYID", "DOMAIN", "USUBJID"],
    "cm": ["STUDYID", "DOMAIN", "USUBJID", "CMSEQ", "CMTRT", "CMDECOD", "CMSTDTC", "CMENDTC"],
}


def _is_missing(series):
    if pd.api.types.is_string_dtype(series) or series.dtype == object:
        return series.isna() | (series.astype(str).str.strip() == "")
    return series.isna()


def _domain_key(domain, columns):
    domain_specific = {
        "sv": ["USUBJID", "VISITNUM"],
        "te": ["STUDYID", "ETCD"],
        "ti": ["STUDYID", "IETESTCD"],
        "ts": ["STUDYID", "TSPARMCD"],
        "tv": ["STUDYID", "ARMCD", "VISITNUM"],
    }
    if domain in domain_specific and all(c in columns for c in domain_specific[domain]):
        return domain_specific[domain]
    seq = f"{domain.upper()}SEQ"
    if "USUBJID" in columns and seq in columns:
        return ["USUBJID", seq]
    if domain.startswith("supp") and all(c in columns for c in ["USUBJID", "RDOMAIN", "QNAM", "IDVARVAL"]):
        return ["USUBJID", "RDOMAIN", "QNAM", "IDVARVAL"]
    if domain == "dm" and "USUBJID" in columns:
        return ["USUBJID"]
    if "USUBJID" in columns:
        return ["USUBJID"]
    if "STUDYID" in columns:
        return ["STUDYID"]
    return []


def _read_domain(path):
    df, meta = pyreadstat.read_sas7bdat(path)
    df.columns = [str(c).upper() for c in df.columns]
    return df, meta


def _profile_domain(path):
    domain = os.path.splitext(os.path.basename(path))[0].lower()
    df, meta = _read_domain(path)
    columns = list(df.columns)
    key = _domain_key(domain, columns)
    duplicate_count = int(df.duplicated(subset=key).sum()) if key else None
    usubjid_n = int(df["USUBJID"].nunique(dropna=True)) if "USUBJID" in df.columns else None
    studyid_n = int(df["STUDYID"].nunique(dropna=True)) if "STUDYID" in df.columns else None
    date_vars = [c for c in columns if c.endswith("DTC") or c.endswith("DT")]
    day_vars = [c for c in columns if c.endswith("DY")]
    week_vars = [c for c in columns if c.endswith("WK") or c.endswith("WKF")]
    expected = [v.upper() for v in EXPECTED_VARIABLES.get(domain, [])]
    present_expected = [v for v in expected if v in columns]
    missing_expected = [v for v in expected if v not in columns]

    variable_rows = []
    for column in columns:
        miss = _is_missing(df[column])
        variable_rows.append({
            "domain": domain,
            "variable": column,
            "type": str(df[column].dtype),
            "missing_n": int(miss.sum()),
            "missing_pct": round(float(miss.mean() * 100), 2) if len(df) else 0.0,
            "nonmissing_n": int((~miss).sum()),
            "distinct_n": int(df[column].nunique(dropna=True)),
            "expected_critical": column in expected,
        })

    domain_row = {
        "domain": domain,
        "file": path,
        "file_size_bytes": os.path.getsize(path),
        "records": int(len(df)),
        "variables": int(len(columns)),
        "usubjid_n": usubjid_n,
        "studyid_n": studyid_n,
        "key": "+".join(key) if key else "",
        "duplicate_key_records": duplicate_count,
        "date_vars_n": len(date_vars),
        "day_vars_n": len(day_vars),
        "week_precision_vars_n": len(week_vars),
        "expected_present_n": len(present_expected),
        "expected_missing_n": len(missing_expected),
        "expected_missing": ", ".join(missing_expected),
    }
    return domain_row, variable_rows


def _write_csv(path, rows, fieldnames):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _md_table(headers, rows):
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for row in rows:
        clean = [str(v).replace("|", "\\|").replace("\n", " ") for v in row]
        lines.append("| " + " | ".join(clean) + " |")
    return "\n".join(lines)


def _build_markdown(generated_at, source_dir, domain_rows, variable_rows, status):
    total_records = sum(r["records"] for r in domain_rows)
    total_bytes = sum(r["file_size_bytes"] for r in domain_rows)
    dm_subjects = next((r["usubjid_n"] for r in domain_rows if r["domain"] == "dm"), None)
    domains_with_dupes = [
        r for r in domain_rows
        if r["duplicate_key_records"] not in (None, 0)
    ]
    domains_with_missing_expected = [r for r in domain_rows if r["expected_missing_n"]]
    high_missing_expected = [
        v for v in variable_rows
        if v["expected_critical"] and v["missing_pct"] >= 20
    ]
    high_missing_expected = sorted(high_missing_expected, key=lambda x: (-x["missing_pct"], x["domain"], x["variable"]))[:30]

    domain_table = [
        [
            r["domain"].upper(),
            r["records"],
            r["variables"],
            "" if r["usubjid_n"] is None else r["usubjid_n"],
            r["key"],
            "" if r["duplicate_key_records"] is None else r["duplicate_key_records"],
            r["date_vars_n"],
            r["week_precision_vars_n"],
            r["expected_missing"],
        ]
        for r in domain_rows
    ]

    lines = [
        "# TROPIC Source Profiling Report",
        "",
        f"Generated: {generated_at}",
        "",
        "> Aggregate-only source profiling evidence. This report does not print patient-level records or subject identifiers.",
        "",
        "## Scope",
        "",
        _md_table(
            ["Item", "Value"],
            [
                ["Source directory", source_dir],
                ["Status", status],
                ["SAS7BDAT domains", len(domain_rows)],
                ["Total records across domains", total_records],
                ["Total source bytes", total_bytes],
                ["DM unique subjects", "" if dm_subjects is None else dm_subjects],
            ],
        ),
        "",
        "## Domain Inventory",
        "",
        _md_table(
            ["Domain", "Records", "Variables", "USUBJID n", "Profile key", "Duplicate key records", "Date vars", "Week precision vars", "Expected missing"],
            domain_table,
        ),
        "",
        "## Source Control Findings",
        "",
    ]

    if domains_with_dupes:
        lines.append("Domains with duplicate records under the profiling key:")
        lines.append("")
        lines.append(_md_table(
            ["Domain", "Key", "Duplicate records"],
            [[r["domain"].upper(), r["key"], r["duplicate_key_records"]] for r in domains_with_dupes],
        ))
    else:
        lines.append("No duplicate records were detected under the selected profiling keys.")

    lines.extend(["", "## Expected Variable Availability", ""])
    if domains_with_missing_expected:
        lines.append(_md_table(
            ["Domain", "Missing expected variables"],
            [[r["domain"].upper(), r["expected_missing"]] for r in domains_with_missing_expected],
        ))
    else:
        lines.append("All configured critical expected variables are present in the profiled domains.")

    lines.extend(["", "## High Missingness Among Critical Expected Variables", ""])
    if high_missing_expected:
        lines.append(_md_table(
            ["Domain", "Variable", "Missing n", "Missing %"],
            [[v["domain"].upper(), v["variable"], v["missing_n"], v["missing_pct"]] for v in high_missing_expected],
        ))
    else:
        lines.append("No configured critical expected variable has missingness >= 20%.")

    lines.extend([
        "",
        "## Timing-Variable Notes",
        "",
        "Date-like variables were detected by `*DTC`/`*DT` suffixes; study-day variables by `*DY`; week-precision variables by `*WK`/`*WKF`.",
        "Week-precision variables should continue to be disclosed in reviewer documentation because they can affect event-time derivations.",
        "",
        "## Machine-Readable Outputs",
        "",
        "- `platform/source_profile_status.json`",
        "- `platform/source_profile/domain_inventory.csv`",
        "- `platform/source_profile/variable_profile.csv`",
        "",
    ])
    return "\n".join(lines)


def build_source_profile(source_dir, out_dir, report_path):
    files = sorted(glob.glob(os.path.join(source_dir, "*.sas7bdat")))
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    os.makedirs(out_dir, exist_ok=True)
    os.makedirs(os.path.dirname(report_path), exist_ok=True)

    if not files:
        status = {
            "status": "not_available",
            "generated_at": generated_at,
            "source_dir": source_dir,
            "reason": "No SAS7BDAT source files found. Real patient-level source data is intentionally external to a clean clone.",
        }
        with open(os.path.join(os.path.dirname(out_dir), "source_profile_status.json"), "w", encoding="utf-8") as f:
            json.dump(status, f, indent=2)
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(_build_markdown(generated_at, source_dir, [], [], "not_available"))
        return status

    domain_rows = []
    variable_rows = []
    for path in files:
        domain_row, domain_variable_rows = _profile_domain(path)
        domain_rows.append(domain_row)
        variable_rows.extend(domain_variable_rows)

    domain_rows = sorted(domain_rows, key=lambda r: r["domain"])
    variable_rows = sorted(variable_rows, key=lambda r: (r["domain"], r["variable"]))

    _write_csv(
        os.path.join(out_dir, "domain_inventory.csv"),
        domain_rows,
        [
            "domain", "file", "file_size_bytes", "records", "variables", "usubjid_n",
            "studyid_n", "key", "duplicate_key_records", "date_vars_n", "day_vars_n",
            "week_precision_vars_n", "expected_present_n", "expected_missing_n", "expected_missing",
        ],
    )
    _write_csv(
        os.path.join(out_dir, "variable_profile.csv"),
        variable_rows,
        ["domain", "variable", "type", "missing_n", "missing_pct", "nonmissing_n", "distinct_n", "expected_critical"],
    )

    status = {
        "status": "pass",
        "generated_at": generated_at,
        "source_dir": source_dir,
        "domains": len(domain_rows),
        "total_records": sum(r["records"] for r in domain_rows),
        "dm_unique_subjects": next((r["usubjid_n"] for r in domain_rows if r["domain"] == "dm"), None),
        "domains_with_duplicate_profile_keys": [
            {"domain": r["domain"], "key": r["key"], "duplicate_key_records": r["duplicate_key_records"]}
            for r in domain_rows if r["duplicate_key_records"] not in (None, 0)
        ],
        "domains_with_missing_expected_variables": [
            {"domain": r["domain"], "expected_missing": r["expected_missing"]}
            for r in domain_rows if r["expected_missing_n"]
        ],
    }
    with open(os.path.join(os.path.dirname(out_dir), "source_profile_status.json"), "w", encoding="utf-8") as f:
        json.dump(status, f, indent=2)
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(_build_markdown(generated_at, source_dir, domain_rows, variable_rows, "pass"))
    return status


def main(argv=None):
    parser = argparse.ArgumentParser(description="Build aggregate source profiling report")
    parser.add_argument("--source-dir", default="01_source_data/real_sdtm")
    parser.add_argument("--out-dir", default="platform/source_profile")
    parser.add_argument("--report", default="docs/SOURCE_PROFILING_REPORT.md")
    args = parser.parse_args(argv)

    status = build_source_profile(args.source_dir, args.out_dir, args.report)
    print(f"Source profile status: {status['status']}")
    print(f"Wrote {args.report}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
