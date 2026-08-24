#!/usr/bin/env python3
"""Load one local CDISC key safely and launch CORE update-cache without a shell."""

from __future__ import annotations

import os
import stat
import subprocess
import sys
import unicodedata
from pathlib import Path
from typing import BinaryIO, Sequence


MAX_CREDENTIAL_BYTES = 16 * 1024
ASSIGNMENT = "CDISC_LIBRARY_API_KEY="


class CredentialError(ValueError):
    """A credential source failed closed validation."""


def _stable_identity(metadata: os.stat_result) -> tuple[int, int, int, int, int]:
    return (
        metadata.st_dev,
        metadata.st_ino,
        metadata.st_size,
        metadata.st_mtime_ns,
        metadata.st_ctime_ns,
    )


def _validate_key(value: str, source: str) -> str:
    if not value:
        raise CredentialError(f"{source} contains an empty CDISC Library API key")
    if any(
        character.isspace() or unicodedata.category(character).startswith("C")
        for character in value
    ):
        raise CredentialError(f"{source} contains whitespace or control characters in the API key")
    return value


def _parse_env_file(payload: bytes) -> str:
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise CredentialError(".core_run/.env is not valid UTF-8") from exc

    assignments: list[str] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if not line.startswith(ASSIGNMENT):
            raise CredentialError(
                f".core_run/.env line {line_number} is not the allowed assignment"
            )
        assignments.append(line[len(ASSIGNMENT) :])
        if len(assignments) > 1:
            raise CredentialError(".core_run/.env contains more than one assignment")
    if len(assignments) != 1:
        raise CredentialError(".core_run/.env must contain exactly one assignment")
    return _validate_key(assignments[0], ".core_run/.env")


def _read_env_file(path: Path) -> str | None:
    no_follow = getattr(os, "O_NOFOLLOW", None)
    directory_only = getattr(os, "O_DIRECTORY", None)
    if no_follow is None or directory_only is None:
        raise CredentialError("platform lacks the required no-follow path controls")
    close_on_exec = getattr(os, "O_CLOEXEC", 0)
    directory_flags = os.O_RDONLY | no_follow | directory_only | close_on_exec
    file_flags = os.O_RDONLY | no_follow | getattr(os, "O_NONBLOCK", 0) | close_on_exec
    try:
        parent_descriptor = os.open(path.parent, directory_flags)
    except OSError as exc:
        raise CredentialError(
            f"cannot open .core_run without following links ({exc.strerror})"
        ) from exc
    try:
        try:
            descriptor = os.open(
                os.fsencode(path.name),
                file_flags,
                dir_fd=parent_descriptor,
            )
        except FileNotFoundError:
            return None
        except OSError as exc:
            raise CredentialError(
                f"cannot open .core_run/.env without following links ({exc.strerror})"
            ) from exc

        try:
            before = os.fstat(descriptor)
            if not stat.S_ISREG(before.st_mode):
                raise CredentialError(".core_run/.env is not a regular file")
            if before.st_uid != os.getuid():
                raise CredentialError(".core_run/.env is not owned by the current user")
            mode = stat.S_IMODE(before.st_mode)
            if mode != 0o600:
                raise CredentialError(
                    f".core_run/.env mode is {mode:04o}; exact mode 0600 is required"
                )
            if before.st_size > MAX_CREDENTIAL_BYTES:
                raise CredentialError(".core_run/.env exceeds the 16 KiB size limit")

            payload = bytearray()
            while len(payload) <= MAX_CREDENTIAL_BYTES:
                chunk = os.read(
                    descriptor,
                    min(4096, MAX_CREDENTIAL_BYTES + 1 - len(payload)),
                )
                if not chunk:
                    break
                payload.extend(chunk)
            if len(payload) > MAX_CREDENTIAL_BYTES:
                raise CredentialError(".core_run/.env exceeds the 16 KiB size limit")
            after = os.fstat(descriptor)
            if _stable_identity(before) != _stable_identity(after):
                raise CredentialError(".core_run/.env changed while it was being read")
        finally:
            os.close(descriptor)

        try:
            current = os.stat(
                os.fsencode(path.name),
                dir_fd=parent_descriptor,
                follow_symlinks=False,
            )
        except OSError as exc:
            raise CredentialError(".core_run/.env disappeared after it was read") from exc
        if (
            not stat.S_ISREG(current.st_mode)
            or current.st_uid != os.getuid()
            or stat.S_IMODE(current.st_mode) != 0o600
            or _stable_identity(current) != _stable_identity(after)
        ):
            raise CredentialError(".core_run/.env was replaced or changed after it was read")
        return _parse_env_file(bytes(payload))
    finally:
        os.close(parent_descriptor)


def _read_inherited_key(stream: BinaryIO) -> str | None:
    payload = stream.read(MAX_CREDENTIAL_BYTES + 1)
    if len(payload) > MAX_CREDENTIAL_BYTES:
        raise CredentialError("inherited CDISC Library API key exceeds the 16 KiB size limit")
    if not payload:
        return None
    try:
        value = payload.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise CredentialError("inherited CDISC Library API key is not valid UTF-8") from exc
    return _validate_key(value, "inherited credential")


def _child_environment(key: str) -> dict[str, str]:
    environment = {
        name: os.environ[name]
        for name in os.environ
        if name not in {"CDISC_LIBRARY_API_KEY", "TROPIC_INHERITED_CDISC_LIBRARY_API_KEY"}
    }
    environment["CDISC_LIBRARY_API_KEY"] = key
    return environment


def main(argv: Sequence[str] | None = None, *, stdin: BinaryIO | None = None) -> int:
    arguments = list(sys.argv[1:] if argv is None else argv)
    if len(arguments) != 4:
        print(
            "usage: run_core_update_cache.py ENV_FILE PYTHON CORE_PY CACHE_DIR",
            file=sys.stderr,
        )
        return 2
    if "CDISC_LIBRARY_API_KEY" in os.environ:
        print("refusing credential-bearing wrapper environment", file=sys.stderr)
        return 2

    env_path, python, core, cache = arguments
    try:
        inherited_key = _read_inherited_key(sys.stdin.buffer if stdin is None else stdin)
        file_key = _read_env_file(Path(env_path))
        key = file_key or inherited_key
        if key is None:
            raise CredentialError(
                "set CDISC_LIBRARY_API_KEY or create an exact-0600 .core_run/.env"
            )
    except CredentialError as exc:
        print(f"refusing CDISC credential input: {exc}", file=sys.stderr)
        return 2

    try:
        result = subprocess.run(
            [python, core, "update-cache", "-c", cache],
            check=False,
            env=_child_environment(key),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
        )
    except OSError as exc:
        print(f"failed to launch CDISC CORE update-cache: {exc}", file=sys.stderr)
        return 2
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
