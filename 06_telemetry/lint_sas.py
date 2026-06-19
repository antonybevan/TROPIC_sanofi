"""Lightweight static analysis for the SAS production track.

This is an advisory style/safety check, NOT a certification of Good Programming
Practice. It hard-fails (exit 1) only on issues that are objectively unsafe for a
portable pipeline - currently hardcoded absolute paths. Everything else (header
block, line length, step/terminator balance) is a non-blocking WARNING. It runs as a
pre-flight gate in cibuild.py and in CI so the ERROR class cannot regress.

Scope/threshold notes:
  * The production *analysis* track only — git/dev helper scripts under
    `02_production_sas/utilities/` are excluded.
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
    
    for i, line in enumerate(lines, 1):
        line_stripped = line.strip()
        line_upper = line_stripped.upper()
        
        # Line length (SAS-traditional 132 cols; quoted-string content exempt — a
        # deliverable title/footnote/label literal cannot be wrapped without changing output)
        bare = re.sub(r'"[^"]*"|\'[^\']*\'|%str\([^)]*\)', '', line.rstrip('\n'))
        if len(bare) > 132:
            warnings.append(f"Line {i}: Exceeds 132 characters (excluding string literals).")
            
        # Hardcoded paths (basic check)
        if re.search(r'([A-Za-z]:\\[^ ]+|/Users/[^ ]+|/home/[^ ]+)', line):
            # Ignore comments
            if not line_stripped.startswith('*') and not line_stripped.startswith('/*'):
                errors.append(f"Line {i}: Hardcoded path detected. Use relative paths or macro variables.")
                
        # Step counting. PROC/DATA are step-starts (line-initial); RUN;/QUIT; are counted
        # ANYWHERE on the line so single-line steps (`data x; set y; run;`) balance correctly.
        if line_upper.startswith("PROC ") and ";" in line_upper:
            proc_count += 1
        elif line_upper.startswith("DATA ") and ";" in line_upper and not line_upper.startswith("DATA ="):
            data_count += 1
        run_quit_count += len(re.findall(r'\b(?:RUN|QUIT)\s*;', line_upper))

    # 3. Missing RUN/QUIT check (Warning)
    total_steps = proc_count + data_count
    if total_steps > run_quit_count:
        warnings.append(f"Possible unclosed steps: Found {total_steps} PROC/DATA statements but only {run_quit_count} RUN/QUIT statements.")

    return errors, warnings

def main():
    print("=== SAS STATIC ANALYSIS (advisory; ERRORS block, WARNINGS advise) ===")
    sas_files = glob.glob("02_production_sas/**/*.sas", recursive=True)
    
    total_errors = 0
    total_warnings = 0
    
    for f in sas_files:
        if "00_config_generated.sas" in f:
            continue
        # Exclude git/dev helper scripts — they are not part of the production analysis track.
        if os.path.sep + "utilities" + os.path.sep in f or "/utilities/" in f:
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
