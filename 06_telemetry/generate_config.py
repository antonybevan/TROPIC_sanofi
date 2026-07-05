"""Generate the SAS macro config included by the production track.

`study_config.yaml` is source-controlled study input, but it is still text that becomes
SAS source code. This generator therefore parses with PyYAML, accepts only a flat scalar
mapping, validates the special date field explicitly, and macro-quotes character values
instead of interpolating raw strings into `%let` statements.
"""
import hashlib
import os
import re
import sys
from datetime import date, datetime

try:
    import yaml
except ImportError:
    yaml = None

_SAS_NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]{0,31}$")


class ConfigError(ValueError):
    """Raised when study_config.yaml cannot be converted into safe SAS macro source."""


def parse_yaml(filepath):
    if yaml is None:
        raise ConfigError("PyYAML is not importable; cannot read study_config.yaml")
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ConfigError(f"malformed YAML in {filepath}: {e}") from e
    if not isinstance(config, dict) or not config:
        raise ConfigError(f"{filepath} must be a non-empty flat key/value mapping")
    out = {}
    for key, val in config.items():
        if not isinstance(key, str) or not _SAS_NAME_RE.match(key):
            raise ConfigError(f"invalid SAS macro variable name in {filepath}: {key!r}")
        if isinstance(val, (dict, list, tuple, set)):
            raise ConfigError(f"{key}: nested/list YAML values are not supported by SAS config generation")
        if val is None:
            raise ConfigError(f"{key}: empty YAML value is not allowed")
        if not isinstance(val, (str, int, float, bool, date)):
            raise ConfigError(f"{key}: unsupported YAML scalar type {type(val).__name__}")
        out[key] = val
    return out


def _format_date(key, val):
    try:
        if isinstance(val, datetime):
            dt = val
        elif isinstance(val, date):
            dt = datetime(val.year, val.month, val.day)
        elif isinstance(val, str):
            dt = datetime.strptime(val, "%Y-%m-%d")
        else:
            raise TypeError
    except (TypeError, ValueError) as e:
        raise ConfigError(f"{key}={val!r} is not a valid YYYY-MM-DD date") from e
    return f"'{dt.strftime('%d%b%Y').upper()}'d"


def _sas_macro_string(key, val):
    text = str(val)
    if "\n" in text or "\r" in text:
        raise ConfigError(f"{key}: string values may not contain newlines")
    if ";" in text:
        raise ConfigError(f"{key}: semicolons are not allowed in generated SAS macro values")
    if text.count('"') % 2 or text.count("'") % 2:
        raise ConfigError(f"{key}: unbalanced quotes are not allowed in generated SAS macro values")
    # Keep the macro variable as text while masking macro triggers (&/%) and operators.
    # Parentheses inside %nrstr() must be marked so a literal ')' cannot close the call.
    masked = text.replace("%", "%%").replace("(", "%(").replace(")", "%)")
    return f"%nrstr({masked})"


def sas_value(key, val):
    if key == "STUDY_CUTOFF_DT":
        return _format_date(key, val)
    if isinstance(val, bool):
        return "1" if val else "0"
    if isinstance(val, (int, float)) and not isinstance(val, bool):
        return str(val)
    return _sas_macro_string(key, val)


def render_sas_config(config):
    lines = [
        "/* ==============================================================================",
        "   Generated automatically from study_config.yaml. Do not edit directly.",
        "   Content-stable output: rewritten only when parsed config changes.",
        "   ============================================================================== */",
        "",
    ]
    for key, val in config.items():
        lines.append(f"%global {key};")
        lines.append(f"%let {key} = {sas_value(key, val)};")
        lines.append("")
    return "\n".join(lines)


def _sha256_text(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def generate_sas_config(config, output_path, exists_fn=os.path.exists, read_fn=None, write_fn=None):
    text = render_sas_config(config)
    read_fn = read_fn or (lambda p: open(p, "r", encoding="utf-8").read())

    def _write(path, content):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)

    write_fn = write_fn or _write
    if exists_fn(output_path):
        current = read_fn(output_path)
        if _sha256_text(current) == _sha256_text(text):
            return False
    write_fn(output_path, text)
    return True


def main():
    # Resolve the study root from the current working directory first (multi-study:
    # cibuild chdirs into the active study root), falling back to the engine location
    # for a standalone/default invocation.
    proj_root = os.getcwd()
    if not os.path.exists(os.path.join(proj_root, "study_config.yaml")):
        proj_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    yaml_path = os.path.join(proj_root, "study_config.yaml")
    sas_out_path = os.path.join(proj_root, "02_production_sas", "00_config_generated.sas")
    
    print(f"Reading configuration from: {yaml_path}")
    try:
        config = parse_yaml(yaml_path)
    except ConfigError as e:
        sys.exit(f"Configuration generation failed: {e}")
    print(f"Generating SAS configuration at: {sas_out_path}")
    try:
        changed = generate_sas_config(config, sas_out_path)
    except ConfigError as e:
        sys.exit(f"Configuration generation failed: {e}")
    print("Configuration generation complete!" if changed else
          "Configuration generation complete: output already current.")

if __name__ == "__main__":
    main()
