"""Pre-flight renv.lock version gate (roadmap Move 2).

activate_renv.R only installs a package when it is ABSENT -- it never checks installed VERSIONS
against renv.lock, and it is not wired into cibuild.py's stage list at all, so a local run's R
environment can silently drift from the locked, CI-restored environment with no signal (CI's
`renv::restore()` in ci.yml does not cover a local `python3 platform/cibuild.py` invocation).

This closes that gap the same way lint_sas.py/generate_config.py already gate the pipeline: a
small deterministic pre-flight script cibuild.py runs and hard-fails on, checked against the
packages activate_renv.R itself requires for the R validation track (not renv.lock's full
transitive closure, which would fail noisily on dev-tooling/version-manager packages never
executed by this pipeline).
"""
import json
import os
import subprocess
import sys

REQUIRED_PACKAGES = [
    "jsonlite", "dplyr", "haven", "lubridate", "ggplot2", "xportr",
    "logrx", "survival", "patchwork", "scales", "diffdf",
]


def _locked_versions(lockfile):
    with open(lockfile, "r", encoding="utf-8") as f:
        lock = json.load(f)
    return {name: rec.get("Version") for name, rec in lock.get("Packages", {}).items()}


def _installed_versions(rscript, packages):
    """One Rscript call returns 'pkg<TAB>version_or_MISSING' per line."""
    probe = (
        "ip <- installed.packages(); pkgs <- c(" +
        ", ".join(f'"{p}"' for p in packages) +
        "); for (p in pkgs) cat(p, '\\t', "
        "if (p %in% rownames(ip)) ip[p, 'Version'] else 'MISSING', '\\n', sep='')"
    )
    out = subprocess.run([rscript, "-e", probe], capture_output=True, text=True)
    versions = {}
    for line in out.stdout.splitlines():
        if "\t" in line:
            pkg, ver = line.split("\t", 1)
            versions[pkg.strip()] = ver.strip()
    return versions


def check(lockfile="renv.lock", rscript=None):
    """Returns (ok, problems, notices)."""
    rscript = rscript or "Rscript"
    if not os.path.exists(lockfile):
        return True, [], [f"{lockfile} not found; skipping renv version gate."]
    locked = _locked_versions(lockfile)
    installed = _installed_versions(rscript, REQUIRED_PACKAGES)

    problems, notices = [], []
    for pkg in REQUIRED_PACKAGES:
        locked_ver = locked.get(pkg)
        if locked_ver is None:
            notices.append(f"{pkg}: not present in {lockfile}; cannot check for drift.")
            continue
        installed_ver = installed.get(pkg, "MISSING")
        if installed_ver == "MISSING":
            problems.append(f"{pkg}: locked at {locked_ver}, but not installed.")
        elif installed_ver != locked_ver:
            problems.append(f"{pkg}: locked at {locked_ver}, but {installed_ver} is installed.")
    return (len(problems) == 0), problems, notices


def main():
    # cibuild.py passes its own resolved RSCRIPT_PATH (argv[1]) so this gate uses the same R
    # install cibuild.py itself would invoke, not whatever bare 'Rscript' happens to resolve to.
    rscript = sys.argv[1] if len(sys.argv) > 1 else None
    ok, problems, notices = check(rscript=rscript)
    for n in notices:
        print(f"  [RENV] NOTE: {n}")
    if not ok:
        print("  [RENV] FAILED: installed R packages have drifted from renv.lock:")
        for p in problems:
            print(f"    - {p}")
        print("  [RENV] Run: Rscript -e \"renv::restore()\"  (or fix the lockfile if the drift is intentional).")
        sys.exit(1)
    print("  [RENV] All required validation packages match renv.lock.")


if __name__ == "__main__":
    main()
