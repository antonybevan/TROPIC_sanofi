#!/usr/bin/env python3
"""
build_ectd_backbone.py - generate the eCTD Module 5 backbone + Study Tagging File
for the TROPIC submission (sequence 0000).

WHY THIS EXISTS
---------------
`m5/` holds the correct FDA Study-Data folder tree and both Define-XML files, but it
is a dataset *package*, not an eCTD *submission*: a tree scan finds no `index.xml`,
no `us-regional.xml`, and no Study Tagging File. FDA requires an STF for every study
in Modules 4/5 (STFs are US-required, not used in EU/JP). This script generates the
missing eCTD backbone layer, wiring the existing `m5/` deliverables with real MD5
checksums and the FDA file-tag vocabulary.

STANDARDS BASIS (researched, not assumed)
-----------------------------------------
- ICH eCTD STF Specification v2.6.1 (2008-06-03): STF root element `ectd:study`,
  DOCTYPE -> STF DTD, `study-identifier` (title/study-id/category) + `study-document`
  with `doc-content`/`file-tag`; leaf model with `checksum`/`checksum-type="MD5"`/
  `operation`; `category name="type-of-control"` for CTD 5.3.5.1.
- ICH eCTD Specification v3.2.2 (2008-07-16): backbone `index.xml`, `index-md5.txt`,
  module-5 heading element names, folder layout (53-clin-stud-rep/535-rep-effic-
  safety-stud/.../5351-stud-rep-contr).
- FDA regional STF (us-stf v2.3) file-tags for datasets, defines, and reviewer guides
  (`analysis-dataset`, `analysis-program`, `analysis-data-definition`,
  `analysis-data-reviewers-guide`, `data-tabulation-dataset`,
  `data-tabulation-data-definition`, `data-tabulation-data-reviewers-guide`,
  `annotated-crf`, `study-report-body`).

OUTPUT  (new, additive - nothing existing is modified)
-----------------------------------------------------
  11_ectd/0000/index.xml                       eCTD backbone
  11_ectd/0000/index-md5.txt                   MD5 of index.xml
  11_ectd/0000/m1/us/us-regional.xml           FDA regional stub (placeholders)
  11_ectd/0000/m5/.../tropic/stf-tropic.xml    Study Tagging File
  11_ectd/0000/util/dtd/README...              which official DTDs to drop in

SCOPE / HONESTY
---------------
- `xlink:href` values are the canonical intra-sequence paths; `checksum` is the real
  MD5 of the corresponding file in the repo `m5/` tree. To finalize a gateway-ready
  sequence, materialize the `m5/` content under `11_ectd/0000/` (package_ectd.py) -
  the hrefs and checksums already target that layout.
- Official ICH/FDA DTDs are NOT fabricated; place them in `util/dtd/` (see README).
- First submission => every leaf `operation="new"`.

USAGE:  python3 06_telemetry/build_ectd_backbone.py
Requires: Python 3 stdlib only.
"""
from __future__ import annotations

import hashlib
import os
from xml.sax.saxutils import escape, quoteattr

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SEQ = "0000"
SEQ_ROOT = os.path.join(ROOT, "11_ectd", SEQ)
M5_SRC = os.path.join(ROOT, "m5")

STUDY_ID = "TROPIC"
STUDY_TITLE = ("A randomized, open-label, multicenter study of cabazitaxel plus "
               "prednisone vs mitoxantrone plus prednisone in mCRPC previously "
               "treated with docetaxel (TROPIC, EFC6193 / NCT00417079)")
# CTD 5.3.5.1 requires a type-of-control category. TROPIC is an active-controlled
# trial (cabazitaxel vs mitoxantrone), no placebo.
TYPE_OF_CONTROL = "active-control-without-placebo"

# eCTD module-5 heading element that holds controlled clinical study reports + data.
M5_ELEMENT = ("m5-3-5-1-study-reports-of-controlled-clinical-studies-"
              "pertinent-to-the-claimed-indication")

# The CTD 5.3.5.1 study leaf containing the STF (canonical intra-sequence location).
STF_DIR_REL = ("m5/53-clin-stud-rep/535-rep-effic-safety-stud/mcrpc/"
               "5351-stud-rep-contr/tropic")
STF_NAME = "stf-tropic.xml"

DTDS_REQUIRED = [
    ("ich-ectd-3-2.dtd", "ICH eCTD backbone DTD v3.2 (https://www.ich.org/) — index.xml"),
    ("ich-stf-v2-2.dtd", "ICH eCTD Study Tagging File DTD v2.2 — stf-tropic.xml"),
    ("us-regional-v3-3.dtd", "FDA US Regional DTD v3.3 (accessdata.fda.gov/static/eCTD/) — us-regional.xml"),
]


def md5_of(path: str) -> str:
    h = hashlib.md5()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def classify(rel: str):
    """Return (file_tag, info_type) per FDA us-stf v2.3, or (None, None) for an
    untagged support file (e.g. a define stylesheet)."""
    p = rel.lower()
    base = os.path.basename(p)
    ext = os.path.splitext(p)[1]
    if base == "adrg.pdf":
        return ("analysis-data-reviewers-guide", "us")
    if base == "sdrg.pdf":
        return ("data-tabulation-data-reviewers-guide", "us")
    if base == "bdrg.pdf":
        return ("data-tabulation-data-reviewers-guide", "us")
    if base == "blankcrf.pdf":
        return ("annotated-crf", "us")
    if base == "define.xml" and "/analysis/adam/" in p:
        return ("analysis-data-definition", "us")
    if base == "define.xml" and "/tabulations/sdtm/" in p:
        return ("data-tabulation-data-definition", "us")
    if base == "adam_spec.xlsx":
        return ("analysis-data-definition", "us")
    if ext == ".xpt" and "/analysis/adam/" in p:
        return ("analysis-dataset", "us")
    if ext == ".xpt" and "/bimo/" in p:
        return ("data-tabulation-dataset", "us")
    if ext == ".xpt" and "/tabulations/sdtm/" in p:
        return ("data-tabulation-dataset", "us")
    if ext in (".sas", ".r") and "/programs/" in p:
        return ("analysis-program", "us")
    if ext == ".pdf" and "/5351-stud-rep-contr/" in p:
        return ("study-report-body", "ich")
    return (None, None)


def collect():
    """Walk m5/ and return ordered content items (skipping TFL appendices, json,
    and anything data-free policy excludes from tagging noise)."""
    skip_dirs = ("/figures", "/tables", "/listings")
    keep_ext = {".xpt", ".sas", ".r", ".pdf", ".xml", ".xsl", ".xlsx"}
    items = []
    for dirpath, _dirs, files in os.walk(M5_SRC):
        reldir = "/" + os.path.relpath(dirpath, ROOT).replace(os.sep, "/").lower()
        if any(s in reldir for s in skip_dirs):
            continue
        for f in files:
            ext = os.path.splitext(f)[1].lower()
            if ext not in keep_ext:
                continue
            src = os.path.join(dirpath, f)
            rel = os.path.relpath(src, ROOT).replace(os.sep, "/")  # 'm5/...'
            tag, info = classify(rel)
            items.append({"src": src, "href": rel, "tag": tag, "info": info,
                          "title": os.path.basename(rel)})
    # deterministic order: category rank, then path
    rank = {"data-tabulation-data-definition": 0, "data-tabulation-dataset": 1,
            "annotated-crf": 2, "data-tabulation-data-reviewers-guide": 3,
            "analysis-data-definition": 4, "analysis-dataset": 5,
            "analysis-program": 6, "analysis-data-reviewers-guide": 7,
            "study-report-body": 8, None: 9}
    items.sort(key=lambda it: (rank.get(it["tag"], 9), it["href"]))
    for i, it in enumerate(items, 1):
        it["id"] = f"L{i:04d}"
    return items


def leaf_xml(it, checksum, indent):
    href = it["href"]
    title = escape(it["title"])
    return (f'{indent}<leaf ID="{it["id"]}" operation="new" xlink:type="simple"\n'
            f'{indent}      xlink:href={quoteattr(href)}\n'
            f'{indent}      checksum-type="MD5" checksum="{checksum}">\n'
            f'{indent}  <title>{title}</title>\n'
            f'{indent}</leaf>\n')


def build_stf(items, stf_path):
    rel_index = os.path.relpath(os.path.join(SEQ_ROOT, "index.xml"),
                                os.path.dirname(stf_path)).replace(os.sep, "/")
    rel_dtd = os.path.relpath(os.path.join(SEQ_ROOT, "util", "dtd", "ich-stf-v2-2.dtd"),
                              os.path.dirname(stf_path)).replace(os.sep, "/")
    rel_style = os.path.relpath(
        os.path.join(SEQ_ROOT, "util", "style", "us-stf-stylesheet.xsl"),
        os.path.dirname(stf_path)).replace(os.sep, "/")
    docs = []
    for it in items:
        if not it["tag"]:
            continue
        ref = f"{rel_index}#{it['id']}"
        docs.append(
            f'    <doc-content xlink:href={quoteattr(ref)}>\n'
            f'      <file-tag name="{it["tag"]}" info-type="{it["info"]}"/>\n'
            f'    </doc-content>')
    body = "\n".join(docs)
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<?xml-stylesheet type="text/xsl" href={quoteattr(rel_style)}?>\n'
        f'<!DOCTYPE ectd:study SYSTEM {quoteattr(rel_dtd)}>\n'
        '<ectd:study xmlns:ectd="http://www.ich.org/ectd" xml:lang="en"\n'
        '            dtd-version="2.2" xmlns:xlink="http://www.w3.org/1999/xlink">\n'
        '  <study-identifier>\n'
        f'    <title>{escape(STUDY_TITLE)}</title>\n'
        f'    <study-id>{escape(STUDY_ID)}</study-id>\n'
        f'    <category name="type-of-control" info-type="ich">{TYPE_OF_CONTROL}</category>\n'
        '  </study-identifier>\n'
        '  <study-document>\n'
        f'{body}\n'
        '  </study-document>\n'
        '</ectd:study>\n'
    )


def build_index(items, checks, regional_href, regional_md5):
    leaves = "".join(leaf_xml(it, checks[it["id"]], "        ") for it in items)
    stf_href = f"{STF_DIR_REL}/{STF_NAME}"
    stf_leaf = (
        '        <leaf ID="Lstf0001" operation="new" xlink:type="simple"\n'
        f'              xlink:href={quoteattr(stf_href)}\n'
        '              version="stf version 2.3"\n'
        f'              checksum-type="MD5" checksum="{checks["Lstf0001"]}">\n'
        '          <title>TROPIC Study Tagging File</title>\n'
        '        </leaf>\n'
    )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<?xml-stylesheet type="text/xsl" href="util/style/ectd-2-0.xsl"?>\n'
        '<!DOCTYPE ectd:ectd SYSTEM "util/dtd/ich-ectd-3-2.dtd">\n'
        '<ectd:ectd xmlns:ectd="http://www.ich.org/ectd"\n'
        # ICH eCTD 3.2 DTD hard-codes (#FIXED) a typo'd xlink URI ("w3c.org"); the value
        # must match the DTD verbatim to be DTD-valid. This is a known eCTD quirk.
        '           xmlns:xlink="http://www.w3c.org/1999/xlink" dtd-version="3.2">\n'
        '  <m1-administrative-information-and-prescribing-information>\n'
        '    <leaf ID="Lreg0001" operation="new" xlink:type="simple"\n'
        f'          xlink:href={quoteattr(regional_href)}\n'
        f'          checksum-type="MD5" checksum="{regional_md5}">\n'
        '      <title>US Regional Information</title>\n'
        '    </leaf>\n'
        '  </m1-administrative-information-and-prescribing-information>\n'
        '  <m5-clinical-study-reports>\n'
        '    <m5-3-clinical-study-reports>\n'
        '      <m5-3-5-reports-of-efficacy-and-safety-studies '
        'indication="metastatic castration-resistant prostate cancer">\n'
        f'        <{M5_ELEMENT}>\n'
        f'{leaves}{stf_leaf}'
        f'        </{M5_ELEMENT}>\n'
        '      </m5-3-5-reports-of-efficacy-and-safety-studies>\n'
        '    </m5-3-clinical-study-reports>\n'
        '  </m5-clinical-study-reports>\n'
        '</ectd:ectd>\n'
    )


def build_regional():
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<?xml-stylesheet type="text/xsl" href="../../util/style/us-regional.xsl"?>\n'
        '<!DOCTYPE fda-regional:fda-regional SYSTEM "../../util/dtd/us-regional-v3-3.dtd">\n'
        # us-regional v3.3 #FIXEDs the ich.org/fda namespace and (like the ICH index DTD) a
        # typo'd xlink URI ("w3c.org"); both must match the DTD verbatim to be DTD-valid.
        '<fda-regional:fda-regional xmlns:fda-regional="http://www.ich.org/fda"\n'
        '                           xmlns:xlink="http://www.w3c.org/1999/xlink"\n'
        '                           xml:lang="en" dtd-version="3.3">\n'
        '  <admin>\n'
        '    <!-- EXAMPLE / DEMONSTRATION metadata - this is NOT a real FDA submission.\n'
        '         "000000" is a placeholder, not an FDA-assigned number. Replace every\n'
        '         applicant + application identifier with the real FDA-assigned values\n'
        '         before any gateway submission. -->\n'
        '    <applicant-info>\n'
        '      <id>EXAMPLE</id>\n'
        '      <company-name>TROPIC Re-Analysis (student demonstration)</company-name>\n'
        '      <applicant-contacts>\n'
        '        <applicant-contact>\n'
        '          <applicant-contact-name applicant-contact-type="regulatory">Example Contact</applicant-contact-name>\n'
        '          <telephones>\n'
        '            <telephone telephone-number-type="work">000-000-0000</telephone>\n'
        '          </telephones>\n'
        '          <emails>\n'
        '            <email>example@example.org</email>\n'
        '          </emails>\n'
        '        </applicant-contact>\n'
        '      </applicant-contacts>\n'
        '    </applicant-info>\n'
        '    <application-set>\n'
        '      <application application-containing-files="true">\n'
        '        <application-information>\n'
        '          <application-number application-type="NDA">000000</application-number>\n'
        '        </application-information>\n'
        '        <submission-information>\n'
        '          <submission-id submission-type="original-application">0000</submission-id>\n'
        '          <sequence-number submission-sub-type="original">0000</sequence-number>\n'
        '        </submission-information>\n'
        '      </application>\n'
        '    </application-set>\n'
        '  </admin>\n'
        '</fda-regional:fda-regional>\n'
    )


def main():
    items = collect()
    os.makedirs(os.path.join(SEQ_ROOT, "m1", "us"), exist_ok=True)
    os.makedirs(os.path.join(SEQ_ROOT, "util", "dtd"), exist_ok=True)
    os.makedirs(os.path.join(SEQ_ROOT, "util", "style"), exist_ok=True)
    stf_path = os.path.join(SEQ_ROOT, STF_DIR_REL, STF_NAME)
    os.makedirs(os.path.dirname(stf_path), exist_ok=True)

    # checksums of real source files (content leaves)
    checks = {it["id"]: md5_of(it["src"]) for it in items}

    # regional stub
    regional_path = os.path.join(SEQ_ROOT, "m1", "us", "us-regional.xml")
    with open(regional_path, "w", encoding="utf-8") as fh:
        fh.write(build_regional())
    regional_md5 = md5_of(regional_path)
    regional_href = "m1/us/us-regional.xml"

    # STF (checksum computed after writing)
    with open(stf_path, "w", encoding="utf-8") as fh:
        fh.write(build_stf(items, stf_path))
    checks["Lstf0001"] = md5_of(stf_path)

    # backbone
    index_path = os.path.join(SEQ_ROOT, "index.xml")
    with open(index_path, "w", encoding="utf-8") as fh:
        fh.write(build_index(items, checks, regional_href, regional_md5))
    with open(os.path.join(SEQ_ROOT, "index-md5.txt"), "w", encoding="utf-8") as fh:
        fh.write(md5_of(index_path) + "\n")

    # util/dtd README — manifest of the official DTDs (ICH/FDA-controlled, not generated here)
    dtd_dir = os.path.join(SEQ_ROOT, "util", "dtd")
    # retire the old "place DTDs here" stub now that they are present
    old_readme = os.path.join(dtd_dir, "README_PLACE_OFFICIAL_DTDS_HERE.txt")
    if os.path.exists(old_readme):
        os.remove(old_readme)
    with open(os.path.join(dtd_dir, "README_DTDS.txt"), "w", encoding="utf-8") as fh:
        fh.write("Official DTDs used to validate this eCTD sequence (ICH/FDA-controlled "
                 "artifacts, not generated by this script):\n\n")
        for name, src in DTDS_REQUIRED:
            present = " [present]" if os.path.exists(os.path.join(dtd_dir, name)) else " [MISSING]"
            fh.write(f"  - {name}: {src}{present}\n")

    tagged = sum(1 for it in items if it["tag"])
    print(f"eCTD sequence {SEQ} written under 11_ectd/{SEQ}/")
    print(f"  content leaves : {len(items)} ({tagged} STF-tagged, "
          f"{len(items) - tagged} untagged support files)")
    print(f"  + STF leaf, + regional leaf")
    print(f"  index-md5.txt  : {md5_of(index_path)}")
    by_tag = {}
    for it in items:
        by_tag[it["tag"]] = by_tag.get(it["tag"], 0) + 1
    for tag, n in sorted(by_tag.items(), key=lambda kv: (kv[0] or "~")):
        print(f"     {tag or '(untagged support)':38} {n}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
