"""Static re-verifier for the committed GREEN-ODA evidence badge (roadmap item 6).

06_telemetry/pipeline_health.json and reconciliation_status.json are LIVE telemetry, overwritten
by every run -- including a sim/--demo run -- so they can never serve as durable proof (audit
C-1). The 06_telemetry/evidence/ snapshot is the durable artifact instead, but a committed
snapshot is only as trustworthy as someone independently re-checking it; otherwise "committed
GREEN" just means "someone once copied GREEN files into git" with no ongoing verification. This
script is that independent check, run as its own CI step so the re-verification is itself on
record, not merely asserted in evidence/README.md.

Two tiers (audit F-14): *_prod.xpt/*_v.xpt are gitignored (real clinical trial data is never
committed), so a fresh clone has nothing to hash the evidence manifest against -- the manifest's
OWN internal consistency, its cross-consistency with the other three evidence files, and its
coverage of the study_manifest.yaml dataset set are all that is staticly checkable without a
data-bearing checkout, and are the ONLY tier that gates the build. This catches accidental
staleness/scope shrinkage, not deliberate fabrication with hand-crafted alternate hashes. If the
actual XPTs are present locally (a data-bearing checkout, or 04_adam/ left over from a prior run),
the hot check re-hashes them against the committed manifest -- but evidence/ is a deliberately
dated, immutable snapshot (see evidence/README.md), so a later codebase/data evolution is EXPECTED
to no longer byte-match it; a hot mismatch is diagnostic information, not a defect, and never
fails this script.
"""
import hashlib
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import manifest

EVIDENCE_DIR = os.path.join(ROOT, "06_telemetry", "evidence")
_ROW_RE = re.compile(
    r"^(?P<ds>\S+)\s+prod\(SAS\)=(?P<prod>[0-9a-f]{32})\s+v\(R\)=(?P<v>[0-9a-f]{32})\s+(?P<tag>\S+)\s*$"
)


def _parse_manifest(path):
    rows, errors = {}, []
    with open(path, "r", encoding="utf-8") as f:
        for n, line in enumerate(f, start=1):
            line = line.rstrip("\n")
            if not line or line.startswith("#"):
                continue
            m = _ROW_RE.match(line)
            if not m:
                errors.append(f"{path}:{n}: unparseable manifest row: {line!r}")
                continue
            rows[m.group("ds")] = {"prod": m.group("prod"), "v": m.group("v"), "tag": m.group("tag")}
    return rows, errors


def _expected_datasets(root=ROOT):
    m = manifest.load_manifest(root=root)
    return set(manifest.dataset_names(m))


def _md5_file(path):
    h = hashlib.md5()  # identity check, not a security use
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def check_static(evidence_dir=EVIDENCE_DIR):
    """(ok, problems) using ONLY the committed evidence files -- never real *.xpt data."""
    problems = []
    manifest_path = os.path.join(evidence_dir, "xpt_md5_manifest.txt")
    if not os.path.exists(manifest_path):
        return False, [f"{manifest_path} not found."]
    rows, parse_errors = _parse_manifest(manifest_path)
    problems.extend(parse_errors)
    if not rows:
        problems.append(f"{manifest_path} has no dataset rows.")
    try:
        expected = _expected_datasets()
        if set(rows) != expected:
            problems.append(f"evidence md5 manifest datasets {sorted(rows)} do not match "
                            f"study_manifest.yaml datasets {sorted(expected)}.")
    except manifest.ManifestError as e:
        problems.append(f"study_manifest.yaml could not be loaded to verify evidence coverage: {e}")

    for ds, row in rows.items():
        if row["tag"] != "DISTINCT":
            problems.append(f"{ds}: manifest tag is {row['tag']!r}, expected DISTINCT.")
        if row["prod"] == row["v"]:
            problems.append(f"{ds}: prod(SAS) and v(R) hashes are IDENTICAL despite a DISTINCT "
                            "tag -- the manifest contradicts its own claim (the sim byte-copy "
                            "signature, not independent double-programming).")

    health_path = os.path.join(evidence_dir, "pipeline_health.oda-green.json")
    if os.path.exists(health_path):
        with open(health_path, "r", encoding="utf-8") as f:
            health = json.load(f)
        if health.get("sas_execution_mode") not in ("oda", "local"):
            problems.append("evidence pipeline_health.oda-green.json: sas_execution_mode="
                            f"{health.get('sas_execution_mode')!r}, expected oda/local.")
        if health.get("pipeline_health_status") != "GREEN":
            problems.append("evidence pipeline_health.oda-green.json: pipeline_health_status "
                            "is not GREEN.")
        pg = health.get("provenance_guard", {})
        if not pg.get("passed"):
            problems.append("evidence pipeline_health.oda-green.json: provenance_guard.passed "
                            "is not true.")
        if set(pg.get("checked_datasets", [])) != set(rows):
            problems.append(f"evidence provenance_guard.checked_datasets {pg.get('checked_datasets')} "
                            f"does not match the md5 manifest's datasets {sorted(rows)}.")
    else:
        problems.append(f"{health_path} not found.")

    recon_path = os.path.join(evidence_dir, "reconciliation_status.oda-green.json")
    if os.path.exists(recon_path):
        with open(recon_path, "r", encoding="utf-8") as f:
            recon = json.load(f)
        if recon.get("overall") != "PASS":
            problems.append("evidence reconciliation_status.oda-green.json: overall is not PASS.")
        domains = {d.lower() for d in recon.get("domains", {})}
        if domains != set(rows):
            problems.append(f"evidence reconciliation domains {sorted(domains)} do not match "
                            f"the md5 manifest's datasets {sorted(rows)}.")
        if any(v != "PASS" for v in recon.get("domains", {}).values()):
            problems.append("evidence reconciliation_status.oda-green.json: a domain is not PASS.")
    else:
        problems.append(f"{recon_path} not found.")

    results_path = os.path.join(evidence_dir, "results_reconciliation_status.oda-green.json")
    if os.path.exists(results_path):
        with open(results_path, "r", encoding="utf-8") as f:
            results = json.load(f)
        if results.get("overall") != "PASS":
            problems.append("evidence results_reconciliation_status.oda-green.json: overall is "
                            "not PASS.")
    else:
        problems.append(f"{results_path} not found.")

    return (len(problems) == 0), problems


def check_hot(evidence_dir=EVIDENCE_DIR, adam_dir=os.path.join(ROOT, "04_adam")):
    """(checked, ok, problems, messages) -- OPTIONAL, DIAGNOSTIC-ONLY: only runs if
    *_prod.xpt/*_v.xpt are actually present locally (a data-bearing checkout or leftover
    04_adam/ from a prior run). Recomputes md5 and reports whether it matches the committed
    manifest EXACTLY. A mismatch is expected once the codebase/data have evolved past the
    snapshot's dated commit and is never treated as a failure by main() -- see the module
    docstring."""
    manifest_path = os.path.join(evidence_dir, "xpt_md5_manifest.txt")
    if not os.path.exists(manifest_path):
        return False, False, [f"{manifest_path} not found."], []
    rows, parse_errors = _parse_manifest(manifest_path)
    if parse_errors:
        return False, False, parse_errors, []
    present = [ds for ds in rows
               if os.path.exists(os.path.join(adam_dir, f"{ds}_prod.xpt"))
               and os.path.exists(os.path.join(adam_dir, f"{ds}_v.xpt"))]
    if not present:
        return False, True, ["no *_prod.xpt/*_v.xpt present locally; hot check skipped (expected "
                             "on a data-free clone/CI checkout -- see audit F-14)."], []
    missing = sorted(set(rows) - set(present))
    messages = [f"checked {len(present)}/{len(rows)} dataset(s) locally."]
    if missing:
        messages.append(f"missing local pairs for: {', '.join(missing)}")
    problems = []
    for ds in present:
        for kind in ("prod", "v"):
            path = os.path.join(adam_dir, f"{ds}_{kind}.xpt")
            actual = _md5_file(path)
            if actual != rows[ds][kind]:
                problems.append(f"{ds} {kind}.xpt: on-disk md5 {actual} != committed manifest "
                                f"{rows[ds][kind]}.")
    return True, (len(problems) == 0), problems, messages


def main():
    ok_static, problems_static = check_static()
    for p in problems_static:
        print(f"  [EVIDENCE STATIC] {p}")
    if ok_static:
        print("  [EVIDENCE STATIC] Internal + cross-file consistency of the committed GREEN-ODA "
              "evidence badge verified.")

    # Diagnostic only -- never gates the build. evidence/ is a deliberately dated, immutable
    # snapshot (see evidence/README.md); a later codebase/data evolution legitimately no longer
    # byte-matches it, so a hot mismatch is informational, not a regression.
    checked_hot, ok_hot, problems_hot, messages_hot = check_hot()
    label = "EVIDENCE HOT" if checked_hot else "EVIDENCE HOT (skipped)"
    for p in problems_hot:
        print(f"  [{label}] {p}")
    for m in messages_hot:
        print(f"  [EVIDENCE HOT] {m}")
    if checked_hot and ok_hot:
        print("  [EVIDENCE HOT] On-disk *_prod.xpt/*_v.xpt md5s match the committed manifest "
              "exactly.")
    elif checked_hot and not ok_hot:
        print("  [EVIDENCE HOT] Mismatch(es) above are expected once the codebase/data have "
              "moved past the snapshot's dated commit; not treated as a failure.")

    if not ok_static:
        sys.exit(1)


if __name__ == "__main__":
    main()
