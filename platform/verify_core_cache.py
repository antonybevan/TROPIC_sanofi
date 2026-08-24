#!/usr/bin/env python3
"""Create or verify the exact downloaded CDISC CORE cache inventory.

The cache itself is intentionally local-only because it is large.  This lock is
the committed provenance record: every direct cache file must be a stable,
regular, no-follow file and must match its recorded SHA-256 and size.  Ordinary
CORE runs verify only; a maintainer must use ``--write`` explicitly and review
the resulting diff when CDISC publishes new cache content.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import secrets
import stat
import sys
from pathlib import Path


SCHEMA = "tropic-cdisc-core-cache-lock/v1"
CORE_VERSION = "0.16.0"
CORE_COMMIT = "c78b05cad21379adf52c8fad5fe1760b826d1ef3"
_CACHE_NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*[.]pkl")


class CacheLockError(RuntimeError):
    """The local cache or committed cache lock is unsafe or inconsistent."""


def _stable_tuple(metadata: os.stat_result) -> tuple[int, int, int, int, int, int]:
    return (
        metadata.st_dev,
        metadata.st_ino,
        metadata.st_mode,
        metadata.st_size,
        metadata.st_mtime_ns,
        metadata.st_ctime_ns,
    )


def build_inventory(cache_dir: Path) -> dict:
    """Hash the exact direct cache inventory without following links."""
    nofollow = getattr(os, "O_NOFOLLOW", 0)
    directory = getattr(os, "O_DIRECTORY", 0)
    close_on_exec = getattr(os, "O_CLOEXEC", 0)
    nonblocking = getattr(os, "O_NONBLOCK", 0)
    if not nofollow or not directory:
        raise CacheLockError("platform lacks O_NOFOLLOW/O_DIRECTORY support")

    directory_fd = _open_real_directory(cache_dir)
    try:
        opened_dir = os.fstat(directory_fd)
        if not stat.S_ISDIR(opened_dir.st_mode):  # pragma: no cover - O_DIRECTORY
            raise CacheLockError("cache path is not a real directory")
        current_dir = os.stat(cache_dir, follow_symlinks=False)
        if (current_dir.st_dev, current_dir.st_ino) != (
            opened_dir.st_dev,
            opened_dir.st_ino,
        ):
            raise CacheLockError("cache directory changed during open")

        names = sorted(os.listdir(directory_fd))
        if not names:
            raise CacheLockError("cache directory is empty")
        rows = []
        for name in names:
            if not _CACHE_NAME.fullmatch(name):
                raise CacheLockError(f"unexpected cache entry: {name!r}")
            file_fd = os.open(
                os.fsencode(name),
                os.O_RDONLY | nofollow | nonblocking | close_on_exec,
                dir_fd=directory_fd,
            )
            try:
                before = os.fstat(file_fd)
                if not stat.S_ISREG(before.st_mode):
                    raise CacheLockError(f"cache entry is not regular: {name!r}")
                digest = hashlib.sha256()
                while True:
                    chunk = os.read(file_fd, 1024 * 1024)
                    if not chunk:
                        break
                    digest.update(chunk)
                after = os.fstat(file_fd)
                if _stable_tuple(before) != _stable_tuple(after):
                    raise CacheLockError(f"cache entry changed while hashing: {name!r}")
                rows.append(
                    {
                        "path": name,
                        "size_bytes": before.st_size,
                        "sha256": digest.hexdigest(),
                    }
                )
            finally:
                os.close(file_fd)

        if sorted(os.listdir(directory_fd)) != names:
            raise CacheLockError("cache directory changed while hashing")
        final_dir = os.fstat(directory_fd)
        if (opened_dir.st_dev, opened_dir.st_ino) != (
            final_dir.st_dev,
            final_dir.st_ino,
        ):
            raise CacheLockError("cache directory identity changed while hashing")
        current_dir = os.stat(cache_dir, follow_symlinks=False)
        if (current_dir.st_dev, current_dir.st_ino) != (
            opened_dir.st_dev,
            opened_dir.st_ino,
        ):
            raise CacheLockError("cache directory was replaced while hashing")
    finally:
        os.close(directory_fd)

    return {
        "schema": SCHEMA,
        "algorithm": "sha256",
        "core_version": CORE_VERSION,
        "core_commit": CORE_COMMIT,
        "inventory_scope": "all direct *.pkl files in resources/cache",
        "file_count": len(rows),
        "files": rows,
    }


def _load_manifest(path: Path) -> dict:
    nofollow = getattr(os, "O_NOFOLLOW", 0)
    close_on_exec = getattr(os, "O_CLOEXEC", 0)
    nonblocking = getattr(os, "O_NONBLOCK", 0)
    if not nofollow:
        raise CacheLockError("platform lacks O_NOFOLLOW support")
    name = path.name
    if not name or name in {".", ".."}:
        raise CacheLockError("cache manifest has an invalid file name")
    parent_fd = _open_real_directory(path.parent)
    try:
        file_fd = os.open(
            os.fsencode(name),
            os.O_RDONLY | nofollow | nonblocking | close_on_exec,
            dir_fd=parent_fd,
        )
        try:
            before = os.fstat(file_fd)
            if not stat.S_ISREG(before.st_mode):
                raise CacheLockError("cache manifest is not a regular file")
            chunks = []
            while True:
                chunk = os.read(file_fd, 1024 * 1024)
                if not chunk:
                    break
                chunks.append(chunk)
            after = os.fstat(file_fd)
            if _stable_tuple(before) != _stable_tuple(after):
                raise CacheLockError("cache manifest changed while reading")
        finally:
            os.close(file_fd)
        current = os.stat(
            os.fsencode(name), dir_fd=parent_fd, follow_symlinks=False
        )
        if _stable_tuple(after) != _stable_tuple(current):
            raise CacheLockError("cache manifest was replaced while reading")
    finally:
        os.close(parent_fd)
    try:
        payload = json.loads(b"".join(chunks).decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CacheLockError(f"cache manifest is not valid UTF-8 JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise CacheLockError("cache manifest root must be an object")
    return payload


def _open_real_directory(path: Path) -> int:
    """Open an absolute directory one no-follow component at a time."""
    nofollow = getattr(os, "O_NOFOLLOW", 0)
    directory = getattr(os, "O_DIRECTORY", 0)
    close_on_exec = getattr(os, "O_CLOEXEC", 0)
    if not nofollow or not directory:
        raise CacheLockError("platform lacks O_NOFOLLOW/O_DIRECTORY support")

    absolute = Path(os.path.abspath(os.fspath(path)))
    parts = absolute.parts
    if not parts or parts[0] != os.path.sep:
        raise CacheLockError("directory path is not an absolute POSIX path")

    flags = os.O_RDONLY | nofollow | directory | close_on_exec
    current_fd = os.open(os.path.sep, flags)
    try:
        for component in parts[1:]:
            next_fd = os.open(os.fsencode(component), flags, dir_fd=current_fd)
            os.close(current_fd)
            current_fd = next_fd
        return current_fd
    except BaseException:
        os.close(current_fd)
        raise


def _write_manifest(path: Path, payload: dict) -> None:
    """Atomically replace a regular manifest without following any link."""
    nofollow = getattr(os, "O_NOFOLLOW", 0)
    close_on_exec = getattr(os, "O_CLOEXEC", 0)
    if not nofollow:
        raise CacheLockError("platform lacks O_NOFOLLOW support")

    name = path.name
    if not name or name in {".", ".."}:
        raise CacheLockError("cache manifest has an invalid file name")
    parent_fd = _open_real_directory(path.parent)
    temp_name = f".{name}.tmp-{secrets.token_hex(16)}"
    temp_created = False
    try:
        try:
            existing = os.stat(
                os.fsencode(name), dir_fd=parent_fd, follow_symlinks=False
            )
        except FileNotFoundError:
            existing = None
        if existing is not None and not stat.S_ISREG(existing.st_mode):
            raise CacheLockError("cache manifest destination is not a regular file")

        flags = (
            os.O_WRONLY
            | os.O_CREAT
            | os.O_EXCL
            | nofollow
            | close_on_exec
        )
        temp_fd = os.open(
            os.fsencode(temp_name), flags, 0o600, dir_fd=parent_fd
        )
        temp_created = True
        try:
            data = (json.dumps(payload, indent=2, sort_keys=False) + "\n").encode(
                "utf-8"
            )
            written = 0
            while written < len(data):
                count = os.write(temp_fd, data[written:])
                if count <= 0:  # pragma: no cover - regular-file writes progress
                    raise CacheLockError("cache manifest write made no progress")
                written += count
            os.fchmod(temp_fd, 0o644)
            os.fsync(temp_fd)
        finally:
            os.close(temp_fd)

        # replace(2) replaces a raced-in leaf symlink rather than following it;
        # the held directory descriptor prevents ancestor substitution.
        os.replace(
            os.fsencode(temp_name),
            os.fsencode(name),
            src_dir_fd=parent_fd,
            dst_dir_fd=parent_fd,
        )
        temp_created = False
        os.fsync(parent_fd)
    finally:
        if temp_created:
            try:
                os.unlink(os.fsencode(temp_name), dir_fd=parent_fd)
            except FileNotFoundError:
                pass
        os.close(parent_fd)


def _cache_is_absent_or_empty(path: Path) -> bool:
    """Return true only for a missing cache or a stable, real empty directory."""
    nofollow = getattr(os, "O_NOFOLLOW", 0)
    directory = getattr(os, "O_DIRECTORY", 0)
    close_on_exec = getattr(os, "O_CLOEXEC", 0)
    if not nofollow or not directory:
        raise CacheLockError("platform lacks O_NOFOLLOW/O_DIRECTORY support")
    name = path.name
    if not name or name in {".", ".."}:
        raise CacheLockError("cache path has an invalid directory name")
    parent_fd = _open_real_directory(path.parent)
    try:
        try:
            before = os.stat(
                os.fsencode(name), dir_fd=parent_fd, follow_symlinks=False
            )
        except FileNotFoundError:
            return True
        if not stat.S_ISDIR(before.st_mode):
            raise CacheLockError("cache path is not a real directory")
        fd = os.open(
            os.fsencode(name),
            os.O_RDONLY | nofollow | directory | close_on_exec,
            dir_fd=parent_fd,
        )
        try:
            opened = os.fstat(fd)
            if (before.st_dev, before.st_ino) != (opened.st_dev, opened.st_ino):
                raise CacheLockError("cache directory changed during open")
            empty = not os.listdir(fd)
            after = os.fstat(fd)
            if (opened.st_dev, opened.st_ino) != (after.st_dev, after.st_ino):
                raise CacheLockError("cache directory identity changed during inspection")
        finally:
            os.close(fd)
        current = os.stat(
            os.fsencode(name), dir_fd=parent_fd, follow_symlinks=False
        )
        if (opened.st_dev, opened.st_ino) != (current.st_dev, current.st_ino):
            raise CacheLockError("cache directory was replaced during inspection")
        return empty
    finally:
        os.close(parent_fd)


def _validate_shape(payload: dict) -> None:
    expected_keys = {
        "schema",
        "algorithm",
        "core_version",
        "core_commit",
        "inventory_scope",
        "file_count",
        "files",
    }
    if set(payload) != expected_keys:
        raise CacheLockError("cache manifest has unexpected top-level fields")
    if payload["schema"] != SCHEMA or payload["algorithm"] != "sha256":
        raise CacheLockError("cache manifest schema or algorithm is unsupported")
    if payload["core_version"] != CORE_VERSION or payload["core_commit"] != CORE_COMMIT:
        raise CacheLockError("cache manifest is bound to a different CORE release")
    files = payload["files"]
    if not isinstance(files, list) or payload["file_count"] != len(files) or not files:
        raise CacheLockError("cache manifest file count is invalid")
    names = []
    for row in files:
        if not isinstance(row, dict) or set(row) != {"path", "size_bytes", "sha256"}:
            raise CacheLockError("cache manifest contains a malformed file row")
        name = row["path"]
        if not isinstance(name, str) or not _CACHE_NAME.fullmatch(name):
            raise CacheLockError(f"cache manifest has an unsafe path: {name!r}")
        if not isinstance(row["size_bytes"], int) or row["size_bytes"] < 0:
            raise CacheLockError(f"cache manifest has an invalid size: {name!r}")
        digest = row["sha256"]
        if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
            raise CacheLockError(f"cache manifest has an invalid SHA-256: {name!r}")
        names.append(name)
    if names != sorted(set(names)):
        raise CacheLockError("cache manifest paths must be unique and sorted")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache", required=True, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument(
        "--write",
        action="store_true",
        help="replace the lock after an explicit reviewed cache refresh",
    )
    parser.add_argument(
        "--allow-initial-empty-cache",
        action="store_true",
        help="permit only a missing/empty first-run cache before download",
    )
    args = parser.parse_args(argv)

    try:
        if args.write and args.allow_initial_empty_cache:
            raise CacheLockError(
                "--write and --allow-initial-empty-cache cannot be combined"
            )
        if args.allow_initial_empty_cache and _cache_is_absent_or_empty(args.cache):
            print("PASS: CDISC CORE cache is absent/empty before first download")
            return 0
        actual = build_inventory(args.cache)
        _validate_shape(actual)
        if args.write:
            _write_manifest(args.manifest, actual)
            print(
                f"WROTE: {args.manifest} ({actual['file_count']} cache files); "
                "review and commit this diff before rerunning CORE"
            )
            return 0

        expected = _load_manifest(args.manifest)
        _validate_shape(expected)
        if actual != expected:
            expected_rows = {row["path"]: row for row in expected["files"]}
            actual_rows = {row["path"]: row for row in actual["files"]}
            missing = sorted(expected_rows.keys() - actual_rows.keys())
            unexpected = sorted(actual_rows.keys() - expected_rows.keys())
            changed = sorted(
                name
                for name in expected_rows.keys() & actual_rows.keys()
                if expected_rows[name] != actual_rows[name]
            )
            raise CacheLockError(
                "cache differs from reviewed lock "
                f"(missing={missing[:5]}, unexpected={unexpected[:5]}, "
                f"changed={changed[:5]}); use --write only after review"
            )
    except (CacheLockError, FileNotFoundError, OSError) as exc:
        print(f"FAIL: CDISC CORE cache lock: {exc}", file=sys.stderr)
        return 1

    print(f"PASS: CDISC CORE cache lock ({actual['file_count']} files)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
