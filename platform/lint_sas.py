"""Lightweight static analysis for the SAS production track.

This is an advisory style/safety check, NOT a certification of Good Programming
Practice. It hard-fails (exit 1) only on issues that are objectively unsafe for a
portable pipeline - currently hardcoded absolute paths. Everything else (header
block, line length, step/terminator balance) is a non-blocking WARNING. It runs as a
pre-flight gate in cibuild.py and in CI so the ERROR class cannot regress.

Scope/threshold notes:
  * The production *analysis* track only — git/dev helper scripts under
    `04_analysis_datasets/programs/sas/utilities/` are excluded.
  * Line length uses the SAS-traditional 132-column standard (the classic LINESIZE
    print width), not an arbitrary 80/120, and ignores quoted-string-literal content
    (`"..."`, `'...'`, `%str(...)`): a title/footnote/label string cannot be wrapped
    without altering the rendered deliverable, so only genuinely long *code* is flagged.
  * Step/terminator balance counts `run;`/`quit;` anywhere on a line (not just at the
    line start) so single-line steps like `data x; set y; run;` are not false-flagged.
"""
import os
import glob
import sys
import re

# Matches a hardcoded absolute filesystem path: a Windows drive-letter path, a Windows UNC path,
# or a POSIX absolute path (token that *starts* with '/') with >=2 segments. Relative
# multi-segment paths like `04_analysis_datasets/programs/sas` must NOT match (the slash
# mid-token is not an absolute root). The first POSIX segment must contain a letter (excludes
# pure dates like 01/15/2024). Leading '/' after ':' or '/' is excluded (URL schemes).
_HARDCODED_PATH_RE = re.compile(
    r'[A-Za-z]:\\[^\s]+'
    r'|\\\\[^\s\\]+\\[^\s]*'
    r'|(?:^|[\s"=])/(?=[^\s/]*[A-Za-z])[^\s/]+/[^\s]*'
)

def _strip_block_comments(line, in_block_comment):
    """Remove /* ... */ comment content from `line`, so a documentation example inside a comment
    is never mistaken for a real hardcoded path -- whether the comment is inline on one line, or
    a multi-line block whose open or close marker sits on a DIFFERENT physical line. `in_block_
    comment` carries that open/closed state across consecutive calls for successive lines in the
    same file. Returns (code_only_text, still_in_block_comment)."""
    out = []
    i, n = 0, len(line)
    while i < n:
        if in_block_comment:
            end = line.find("*/", i)
            if end == -1:
                break  # rest of line is comment; stays open for the next line
            in_block_comment = False
            i = end + 2
        else:
            start = line.find("/*", i)
            if start == -1:
                out.append(line[i:])
                break
            out.append(line[i:start])
            end = line.find("*/", start + 2)
            if end == -1:
                in_block_comment = True
                break
            i = end + 2
    return "".join(out), in_block_comment

def lint_sas_file(filepath):
    errors = []
    warnings = []
    
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()
        
    if not lines:
        return errors, warnings
        
    # 1. Header block check
    header = "".join(lines[:10]).upper()
    if "PROGRAM:" not in header and "DESCRIPTION:" not in header:
        warnings.append("Missing standard header block ('Program:' or 'Description:') in the first 10 lines.")
        
    # 2. Line length and hardcoded paths
    proc_count = 0
    data_count = 0
    run_quit_count = 0
    in_block_comment = False  # tracks an OPEN /* ... */ that spans multiple lines
    pending_data_open = False  # tracks a DATA statement whose opener has no ';' on this line yet

    for i, line in enumerate(lines, 1):
        line_stripped = line.strip()
        line_upper = line_stripped.upper()

        # Line length (SAS-traditional 132 cols; quoted-string content exempt — a
        # deliverable title/footnote/label literal cannot be wrapped without changing output)
        bare = re.sub(r'"[^"]*"|\'[^\']*\'|%str\([^)]*\)', '', line.rstrip('\n'))
        if len(bare) > 132:
            warnings.append(f"Line {i}: Exceeds 132 characters (excluding string literals).")

        # Hardcoded paths: strip /* ... */ comment content first (inline AND multi-line spans),
        # so a documentation example inside a comment is never mistaken for real code. SAS's
        # OTHER comment style (a statement starting with '*') is still only recognized when it
        # starts the line, same as before.
        code_for_path_check, in_block_comment = _strip_block_comments(line, in_block_comment)
        if not line_stripped.startswith('*') and _HARDCODED_PATH_RE.search(code_for_path_check):
            errors.append(f"Line {i}: Hardcoded path detected. Use relative paths or macro variables.")

        # Step counting. PROC/DATA are step-starts (line-initial); RUN;/QUIT; are counted
        # ANYWHERE on the line so single-line steps (`data x; set y; run;`) balance correctly.
        # A DATA statement's opener can itself span multiple lines before its first ';' (e.g. a
        # dataset option list: `data adam.adsl\n    (label="...");`) -- pending_data_open tracks
        # that continuation across lines the same way in_block_comment tracks an open /* */, so
        # such a step is still counted once its closing ';' is found, not silently dropped.
        if pending_data_open:
            if ";" in line_upper:
                data_count += 1
                pending_data_open = False
        elif line_upper.startswith("PROC ") and ";" in line_upper:
            proc_count += 1
        elif line_upper.startswith("DATA ") and not line_upper.startswith("DATA ="):
            if ";" in line_upper:
                data_count += 1
            else:
                pending_data_open = True
        run_quit_count += len(re.findall(r'\b(?:RUN|QUIT)\s*;', line_upper))

    # 3. Missing RUN/QUIT check (Warning)
    total_steps = proc_count + data_count
    if total_steps > run_quit_count:
        warnings.append(f"Possible unclosed steps: Found {total_steps} PROC/DATA statements but only {run_quit_count} RUN/QUIT statements.")

    return errors, warnings

def main():
    print("=== SAS STATIC ANALYSIS (advisory; ERRORS block, WARNINGS advise) ===")
    sas_files = glob.glob("04_analysis_datasets/programs/sas/**/*.sas", recursive=True)
    
    total_errors = 0
    total_warnings = 0
    
    for f in sas_files:
        if "00_config_generated.sas" in f:
            continue
        # Exclude git/dev helper scripts — they are not part of the production analysis track.
        # Tests actual path COMPONENTS (via normpath + split), not a substring match against two
        # separately-enumerated separator conventions, so it's correct on both POSIX and Windows
        # (glob's recursive=True can return either separator there) without hardcoding a fallback.
        if "utilities" in os.path.normpath(f).split(os.path.sep):
            continue
            
        errs, warns = lint_sas_file(f)
        total_errors += len(errs)
        total_warnings += len(warns)
        
        if errs or warns:
            print(f"\nFile: {f}")
            for w in warns:
                print(f"  [WARNING] {w}")
            for e in errs:
                print(f"  [ERROR] {e}")
                
    print(f"\nLinting Complete: {total_errors} blocking error(s), "
          f"{total_warnings} advisory warning(s) across {len(sas_files)} files.")

    if total_errors > 0:
        print("FAIL: blocking static-analysis error(s) - see [ERROR] lines above.")
        sys.exit(1)
    print("PASS: no blocking static-analysis errors.")
    sys.exit(0)

if __name__ == "__main__":
    main()
