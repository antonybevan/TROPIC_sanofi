#!/usr/bin/env python3
"""Verify the exact local CDISC CORE source tree before executing it.

The pinned upstream checkout is local-only and its downloaded cache is mutable.
This verifier requires the exact commit, permits only the separately governed
``resources/cache`` drift, and applies/accepts one deterministic ADaM CLI
compatibility patch.  Any other tracked or untracked executable source fails
closed before a CDISC Library credential is passed to CORE.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import re
import secrets
import stat
import subprocess
import sys
from pathlib import Path, PurePosixPath


PATCH_PATH = "cdisc_rules_engine/enums/standard_types.py"
CACHE_PREFIX = "resources/cache/"
ORIGINAL_BLOCK = b'    ADAM = "adam"\n    TIG = "tig"\n'
PATCHED_BLOCK = b'''    ADAM = "adam"
    # ADaM IG/product names. normalize_adam_input() (utilities/utils.py) maps these to
    # standards/adam/<product>-<v>, and ADAM_PRODUCTS (constants/adam_products.py) lists
    # them, but the CLI StandardTypes gate omitted them -- so a documented `-s adamig`
    # invocation was rejected before reaching the engine. Mirror ADAM_PRODUCTS here.
    ADAMIG = "adamig"
    ADAM_ADAE = "adam-adae"
    ADAM_MD = "adam-md"
    ADAM_NCA = "adam-nca"
    ADAM_OCCDS = "adam-occds"
    ADAM_TTE = "adam-tte"
    ADAM_POPPK = "adam-poppk"
    TIG = "tig"
'''


class SourceLockError(RuntimeError):
    """The local CORE checkout is not the reviewed executable source."""


def _git(engine: Path, *args: str) -> bytes:
    environment = {
        name: value
        for name, value in os.environ.items()
        if not name.startswith("GIT_")
    }
    # The pinned object must be interpreted literally. Local replace refs,
    # alternate object stores, and inherited Git configuration are not part of
    # the reviewed source authority.
    environment.update(
        {
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_NO_REPLACE_OBJECTS": "1",
            "GIT_OPTIONAL_LOCKS": "0",
            "GIT_TERMINAL_PROMPT": "0",
        }
    )
    result = subprocess.run(
        ["git", "-c", "core.hooksPath=/dev/null", "-C", os.fspath(engine), *args],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=environment,
    )
    if result.returncode:
        detail = result.stderr.decode("utf-8", errors="replace").strip()
        raise SourceLockError(f"git {' '.join(args)} failed: {detail}")
    return result.stdout


def _nul_paths(data: bytes) -> list[str]:
    try:
        return [
            item.decode("utf-8")
            for item in data.split(b"\0")
            if item
        ]
    except UnicodeDecodeError as exc:
        raise SourceLockError("CORE Git path is not valid UTF-8") from exc


def _safe_parts(path: str) -> tuple[str, ...]:
    candidate = PurePosixPath(path)
    if (
        not path
        or candidate.is_absolute()
        or candidate.as_posix() != path
        or not candidate.parts
        or any(part in {"", ".", ".."} for part in candidate.parts)
    ):
        raise SourceLockError(f"CORE tree contains an unsafe path: {path!r}")
    return candidate.parts


def _stable_tuple(metadata: os.stat_result) -> tuple[int, int, int, int, int, int]:
    return (
        metadata.st_dev,
        metadata.st_ino,
        metadata.st_mode,
        metadata.st_size,
        metadata.st_mtime_ns,
        metadata.st_ctime_ns,
    )


def _open_real_directory(path: Path) -> int:
    """Open an absolute directory one no-follow component at a time."""
    nofollow = getattr(os, "O_NOFOLLOW", 0)
    directory = getattr(os, "O_DIRECTORY", 0)
    close_on_exec = getattr(os, "O_CLOEXEC", 0)
    if not nofollow or not directory:
        raise SourceLockError("platform lacks O_NOFOLLOW/O_DIRECTORY support")

    absolute = Path(os.path.abspath(os.fspath(path)))
    parts = absolute.parts
    if not parts or parts[0] != os.path.sep:
        raise SourceLockError("CORE engine path is not an absolute POSIX path")
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


def _open_parent(engine_fd: int, rel_path: str) -> tuple[int, bytes]:
    parts = _safe_parts(rel_path)
    nofollow = getattr(os, "O_NOFOLLOW", 0)
    directory = getattr(os, "O_DIRECTORY", 0)
    close_on_exec = getattr(os, "O_CLOEXEC", 0)
    if not nofollow or not directory:
        raise SourceLockError("platform lacks O_NOFOLLOW/O_DIRECTORY support")
    current_fd = os.dup(engine_fd)
    flags = os.O_RDONLY | nofollow | directory | close_on_exec
    try:
        for component in parts[:-1]:
            next_fd = os.open(os.fsencode(component), flags, dir_fd=current_fd)
            os.close(current_fd)
            current_fd = next_fd
        return current_fd, os.fsencode(parts[-1])
    except BaseException:
        os.close(current_fd)
        raise


def _read_leaf(parent_fd: int, leaf: bytes, rel_path: str) -> tuple[bytes, os.stat_result]:
    nofollow = getattr(os, "O_NOFOLLOW", 0)
    nonblocking = getattr(os, "O_NONBLOCK", 0)
    close_on_exec = getattr(os, "O_CLOEXEC", 0)
    if not nofollow:
        raise SourceLockError("platform lacks O_NOFOLLOW support")
    file_fd = os.open(
        leaf,
        os.O_RDONLY | nofollow | nonblocking | close_on_exec,
        dir_fd=parent_fd,
    )
    try:
        before = os.fstat(file_fd)
        if not stat.S_ISREG(before.st_mode):
            raise SourceLockError(f"CORE source is not regular: {rel_path}")
        chunks = []
        while True:
            chunk = os.read(file_fd, 1024 * 1024)
            if not chunk:
                break
            chunks.append(chunk)
        after = os.fstat(file_fd)
        if _stable_tuple(before) != _stable_tuple(after):
            raise SourceLockError(f"CORE source changed while reading: {rel_path}")
    finally:
        os.close(file_fd)
    current = os.stat(leaf, dir_fd=parent_fd, follow_symlinks=False)
    if _stable_tuple(after) != _stable_tuple(current):
        raise SourceLockError(f"CORE source was replaced while reading: {rel_path}")
    return b"".join(chunks), after


def _read_regular(engine_fd: int, rel_path: str) -> tuple[bytes, os.stat_result]:
    parent_fd, leaf = _open_parent(engine_fd, rel_path)
    try:
        return _read_leaf(parent_fd, leaf, rel_path)
    finally:
        os.close(parent_fd)


def _atomic_replace_regular(
    engine_fd: int,
    rel_path: str,
    expected_before: bytes,
    data: bytes,
    mode: int,
) -> None:
    """Replace one verified engine-relative file without following links."""
    nofollow = getattr(os, "O_NOFOLLOW", 0)
    close_on_exec = getattr(os, "O_CLOEXEC", 0)
    if not nofollow:
        raise SourceLockError("platform lacks O_NOFOLLOW support")
    parent_fd, leaf = _open_parent(engine_fd, rel_path)
    temp_name = os.fsencode(f".{os.fsdecode(leaf)}.tropic-{secrets.token_hex(16)}")
    temp_created = False
    try:
        current_bytes, current_meta = _read_leaf(parent_fd, leaf, rel_path)
        if current_bytes != expected_before:
            raise SourceLockError(f"CORE source changed before patching: {rel_path}")
        temp_fd = os.open(
            temp_name,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | nofollow | close_on_exec,
            0o600,
            dir_fd=parent_fd,
        )
        temp_created = True
        try:
            written = 0
            while written < len(data):
                count = os.write(temp_fd, data[written:])
                if count <= 0:  # pragma: no cover - regular-file writes progress
                    raise SourceLockError("CORE compatibility patch write stalled")
                written += count
            os.fchmod(temp_fd, mode)
            os.fsync(temp_fd)
        finally:
            os.close(temp_fd)
        current = os.stat(leaf, dir_fd=parent_fd, follow_symlinks=False)
        if _stable_tuple(current) != _stable_tuple(current_meta):
            raise SourceLockError(f"CORE source changed before replacement: {rel_path}")
        os.replace(
            temp_name,
            leaf,
            src_dir_fd=parent_fd,
            dst_dir_fd=parent_fd,
        )
        temp_created = False
        os.fsync(parent_fd)
        replaced, _ = _read_leaf(parent_fd, leaf, rel_path)
        if replaced != data:
            raise SourceLockError(f"CORE source patch verification failed: {rel_path}")
    finally:
        if temp_created:
            try:
                os.unlink(temp_name, dir_fd=parent_fd)
            except FileNotFoundError:
                pass
        os.close(parent_fd)


def _tree_entries(engine: Path, commit: str) -> dict[str, tuple[str, str]]:
    entries: dict[str, tuple[str, str]] = {}
    for record in _git(engine, "ls-tree", "-rz", "--full-tree", commit).split(b"\0"):
        if not record:
            continue
        try:
            header, encoded_path = record.split(b"\t", 1)
            mode, object_type, object_id = header.decode("ascii").split()
            path = encoded_path.decode("utf-8")
        except (ValueError, UnicodeDecodeError) as exc:
            raise SourceLockError("CORE commit tree contains a malformed entry") from exc
        _safe_parts(path)
        if object_type != "blob" or mode not in {"100644", "100755"}:
            raise SourceLockError(
                f"CORE commit tree contains a link, submodule, or unsupported mode: {path}"
            )
        if not re.fullmatch(r"[0-9a-f]{40}", object_id) or path in entries:
            raise SourceLockError(f"CORE commit tree contains an invalid entry: {path}")
        entries[path] = (mode, object_id)
    if PATCH_PATH not in entries:
        raise SourceLockError("pinned CORE tree omits the compatibility source")
    return entries


def _index_entries(engine: Path) -> dict[str, tuple[str, str]]:
    entries: dict[str, tuple[str, str]] = {}
    for record in _git(engine, "ls-files", "--stage", "-z").split(b"\0"):
        if not record:
            continue
        try:
            header, encoded_path = record.split(b"\t", 1)
            mode, object_id, stage = header.decode("ascii").split()
            path = encoded_path.decode("utf-8")
        except (ValueError, UnicodeDecodeError) as exc:
            raise SourceLockError("CORE index contains a malformed entry") from exc
        _safe_parts(path)
        if stage != "0" or path in entries or not re.fullmatch(r"[0-9a-f]{40}", object_id):
            raise SourceLockError(f"CORE index contains an unresolved or invalid entry: {path}")
        entries[path] = (mode, object_id)
    return entries


def _git_blob_id(payload: bytes) -> str:
    framed = f"blob {len(payload)}\0".encode("ascii") + payload
    return hashlib.sha1(framed, usedforsecurity=False).hexdigest()


def _expected_patch(
    engine: Path, tree: dict[str, tuple[str, str]]
) -> tuple[bytes, bytes]:
    pristine = _git(engine, "cat-file", "blob", tree[PATCH_PATH][1])
    if pristine.count(ORIGINAL_BLOCK) != 1:
        raise SourceLockError("pinned CORE source has an unexpected StandardTypes shape")
    return pristine, pristine.replace(ORIGINAL_BLOCK, PATCHED_BLOCK, 1)


def _untracked_paths(engine: Path) -> list[str]:
    ordinary = _nul_paths(
        _git(engine, "ls-files", "--others", "--exclude-standard", "-z")
    )
    ignored = _nul_paths(
        _git(
            engine,
            "ls-files",
            "--others",
            "--ignored",
            "--exclude-standard",
            "-z",
        )
    )
    return sorted(set(ordinary) | set(ignored))


def _verify_worktree(
    engine_fd: int,
    tree: dict[str, tuple[str, str]],
    pristine_patch: bytes,
    expected_patch: bytes,
) -> tuple[bytes, int]:
    patch_state: tuple[bytes, int] | None = None
    for path, (expected_mode, expected_object) in sorted(tree.items()):
        if path.startswith(CACHE_PREFIX):
            continue
        try:
            payload, metadata = _read_regular(engine_fd, path)
        except OSError as exc:
            raise SourceLockError(
                f"CORE tracked source cannot be opened safely: {path} ({exc.strerror})"
            ) from exc
        actual_executable = bool(stat.S_IMODE(metadata.st_mode) & 0o111)
        expected_executable = expected_mode == "100755"
        if actual_executable != expected_executable:
            raise SourceLockError(f"CORE tracked source mode differs: {path}")
        if path == PATCH_PATH:
            if payload not in {pristine_patch, expected_patch}:
                raise SourceLockError("CORE ADaM compatibility file has unreviewed changes")
            patch_state = (payload, stat.S_IMODE(metadata.st_mode))
        elif _git_blob_id(payload) != expected_object:
            raise SourceLockError(f"CORE tracked source differs from pinned commit: {path}")
    if patch_state is None:
        raise SourceLockError("CORE compatibility source was not verified")
    return patch_state


def verify(engine: Path, commit: str) -> None:
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise SourceLockError("CORE commit must be a full lowercase SHA-1")
    engine_fd = _open_real_directory(engine)
    try:
        opened_engine = os.fstat(engine_fd)
        head = _git(engine, "rev-parse", "HEAD").decode("ascii").strip()
        if head != commit:
            raise SourceLockError(f"CORE HEAD differs from reviewed commit {commit}")

        tree = _tree_entries(engine, commit)
        index = _index_entries(engine)
        if index != tree:
            missing = sorted(tree.keys() - index.keys())
            unexpected = sorted(index.keys() - tree.keys())
            changed = sorted(
                path
                for path in tree.keys() & index.keys()
                if tree[path] != index[path]
            )
            raise SourceLockError(
                "CORE index differs from pinned commit "
                f"(missing={missing[:5]}, unexpected={unexpected[:5]}, changed={changed[:5]})"
            )

        pristine, expected = _expected_patch(engine, tree)
        current, mode = _verify_worktree(engine_fd, tree, pristine, expected)
        unexpected_untracked = [
            path
            for path in _untracked_paths(engine)
            if not path.startswith(CACHE_PREFIX)
        ]
        if unexpected_untracked:
            raise SourceLockError(
                f"CORE checkout has untracked or ignored files: {unexpected_untracked[:5]}"
            )

        # Mutate only after the complete pinned tree, index, and extra-file
        # inventory have been validated. The descriptor-relative writer cannot
        # escape through a checkout symlink.
        if current == pristine:
            _atomic_replace_regular(
                engine_fd, PATCH_PATH, pristine, expected, mode
            )

        # Recheck the complete executable surface after patching to reduce the
        # verifier-to-execution race and prove the final accepted state.
        final_patch, _ = _verify_worktree(engine_fd, tree, pristine, expected)
        if final_patch != expected:
            raise SourceLockError("CORE compatibility patch is not in its final state")
        final_untracked = [
            path
            for path in _untracked_paths(engine)
            if not path.startswith(CACHE_PREFIX)
        ]
        if final_untracked:
            raise SourceLockError(
                f"CORE checkout changed during verification: {final_untracked[:5]}"
            )
        current_engine = os.stat(engine, follow_symlinks=False)
        if (
            not stat.S_ISDIR(current_engine.st_mode)
            or (current_engine.st_dev, current_engine.st_ino)
            != (opened_engine.st_dev, opened_engine.st_ino)
        ):
            raise SourceLockError("CORE engine directory was replaced during verification")
    finally:
        os.close(engine_fd)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--engine", required=True, type=Path)
    parser.add_argument("--commit", required=True)
    args = parser.parse_args(argv)
    try:
        verify(args.engine, args.commit)
    except (SourceLockError, FileNotFoundError, OSError) as exc:
        print(f"FAIL: CDISC CORE source lock: {exc}", file=sys.stderr)
        return 1
    print(f"PASS: CDISC CORE source lock ({args.commit[:12]})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
