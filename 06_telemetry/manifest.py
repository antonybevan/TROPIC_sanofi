"""Study-manifest loader (I/J platform generalisation, Phase 0).

The manifest (study_manifest.yaml at the study root) declares pipeline STRUCTURE —
the reconciled datasets, their business keys, the program wiring, and the study
identity — so the orchestrator and reconciler no longer hardcode it. This is the
structural companion to study_config.yaml (clinical parameters).

pyyaml is used deliberately: the manifest is nested (the flat parser in
generate_config.py cannot express it), pyyaml is already a CI dependency, and the
R side already reads YAML via the `yaml` package. Callers that must never hard-fail
on a missing/malformed manifest should catch ManifestError and fall back to their
legacy hardcoded list (see cibuild.py).
"""
import os

try:
    import yaml
except ImportError:  # surfaced as ManifestError at load time, not import time
    yaml = None

DEFAULT_MANIFEST_NAME = "study_manifest.yaml"


class ManifestError(Exception):
    """Raised when the manifest cannot be located, parsed, or is missing required keys."""


def manifest_path(study=None, root="."):
    """Resolve the manifest path.

    Phase 0: the study root is the repo root, so this returns
    `<root>/study_manifest.yaml`. Phase 2 extends this to resolve a named study
    under studies/<study>/ — kept as a single chokepoint so that change is local.
    """
    if study:
        return os.path.join(root, "studies", study, DEFAULT_MANIFEST_NAME)
    return os.path.join(root, DEFAULT_MANIFEST_NAME)


def load_manifest(path=None, study=None, root="."):
    """Load and minimally validate the manifest. Raises ManifestError on any problem."""
    if yaml is None:
        raise ManifestError("pyyaml is not importable; cannot read the study manifest")
    path = path or manifest_path(study=study, root=root)
    if not os.path.exists(path):
        raise ManifestError(f"manifest not found: {path}")
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:  # type: ignore[union-attr]
        raise ManifestError(f"malformed manifest {path}: {e}")
    if not isinstance(data, dict) or "datasets" not in data or "study" not in data:
        raise ManifestError(f"manifest {path} missing required 'study'/'datasets' keys")
    return data


def dataset_names(manifest):
    """Ordered list of reconciled dataset member names (e.g. adsl, ..., clinsite)."""
    return [d["name"] for d in manifest["datasets"]]


def business_keys(manifest):
    """Map of dataset name -> list of business keys used by the reconciler."""
    return {d["name"]: list(d.get("keys", [])) for d in manifest["datasets"]}


def study_identity(manifest):
    """Study identity dict with id/code/title (missing fields default to empty)."""
    s = manifest.get("study", {}) or {}
    return {"id": s.get("id", ""), "code": s.get("code", ""), "title": s.get("title", "")}


def study_label(manifest):
    """Human banner label, e.g. 'TROPIC (Study EFC6193 / XRP6258)'."""
    ident = study_identity(manifest)
    return f"{ident['title']} (Study {ident['code']})"


def results_recon_specs(manifest):
    """Datasets carrying a results_recon block (Phase 1 consumes this)."""
    return {d["name"]: d["results_recon"]
            for d in manifest["datasets"] if d.get("results_recon")}
