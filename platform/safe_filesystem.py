"""Fail-closed filesystem primitives for controlled packaging workflows.

The release tools process local, partly Git-ignored clinical artifacts. Lexical
containment is not an authorization boundary, and a check-then-open sequence is
not sufficient when another process can replace an ancestor. These primitives
therefore pin every directory component with a descriptor, use ``O_NOFOLLOW``
for traversal and file opens, and perform mutations relative to pinned parent
descriptors.
"""

from __future__ import annotations

import fnmatch
import hashlib
import json
import os
import secrets
import shutil
import stat
from contextlib import contextmanager
from pathlib import Path, PurePosixPath
from typing import Iterator


class UnsafePathError(RuntimeError):
    """Raised when a controlled filesystem path is missing, linked, or escaping."""


class _MissingControlledPath(FileNotFoundError):
    """Internal signal used by the non-raising existence predicates."""


def _absolute(path: str | os.PathLike[str]) -> Path:
    return Path(os.path.abspath(os.fspath(path)))


def _directory_flags() -> int:
    if not hasattr(os, "O_DIRECTORY") or not hasattr(os, "O_NOFOLLOW"):
        raise UnsafePathError(
            "descriptor-relative O_DIRECTORY/O_NOFOLLOW support is required"
        )
    return (
        os.O_RDONLY
        | os.O_DIRECTORY
        | os.O_NOFOLLOW
        | getattr(os, "O_CLOEXEC", 0)
    )


def _file_read_flags() -> int:
    if not hasattr(os, "O_NOFOLLOW"):
        raise UnsafePathError("descriptor-relative O_NOFOLLOW support is required")
    return os.O_RDONLY | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0)


def _entry_info(parent_fd: int, name: str, display: Path) -> os.stat_result:
    try:
        return os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
    except FileNotFoundError as exc:
        raise _MissingControlledPath(str(display)) from exc
    except OSError as exc:
        raise UnsafePathError(f"cannot inspect controlled path {display}: {exc}") from exc


def _reject_link(info: os.stat_result, display: Path, *, destination: bool = False) -> None:
    if stat.S_ISLNK(info.st_mode):
        kind = "destination" if destination else "controlled"
        raise UnsafePathError(f"symlinked {kind} path is forbidden: {display}")


def _stable_file_signature(info: os.stat_result) -> tuple[int, ...]:
    """Metadata that must not change while a controlled regular file is read.

    Access time is deliberately excluded because the read itself may update it.
    Change time is included so an in-place writer cannot hide a same-size update by
    restoring the modification timestamp.
    """
    return (
        info.st_dev,
        info.st_ino,
        info.st_mode,
        info.st_nlink,
        info.st_uid,
        info.st_gid,
        info.st_size,
        info.st_mtime_ns,
        info.st_ctime_ns,
    )


def _open_directory_entry(
    parent_fd: int,
    name: str,
    display: Path,
    *,
    create: bool = False,
    mode: int = 0o755,
) -> int:
    try:
        info = _entry_info(parent_fd, name, display)
    except _MissingControlledPath:
        if not create:
            raise
        try:
            os.mkdir(name, mode=mode, dir_fd=parent_fd)
        except FileExistsError:
            # A racing creator is acceptable only if the no-follow open below
            # proves that it created a real directory.
            pass
        except OSError as exc:
            raise UnsafePathError(
                f"cannot create controlled directory {display}: {exc}"
            ) from exc
        info = _entry_info(parent_fd, name, display)

    _reject_link(info, display)
    if not stat.S_ISDIR(info.st_mode):
        raise UnsafePathError(f"controlled path is not a directory: {display}")
    try:
        descriptor = os.open(name, _directory_flags(), dir_fd=parent_fd)
    except OSError as exc:
        raise UnsafePathError(
            f"cannot open controlled directory without following a symlink: {display}: {exc}"
        ) from exc
    opened = os.fstat(descriptor)
    if (
        not stat.S_ISDIR(opened.st_mode)
        or (opened.st_dev, opened.st_ino) != (info.st_dev, info.st_ino)
    ):
        os.close(descriptor)
        raise UnsafePathError(f"controlled directory changed while opening: {display}")
    return descriptor


def _open_regular_entry(parent_fd: int, name: str, display: Path) -> int:
    info = _entry_info(parent_fd, name, display)
    _reject_link(info, display)
    if not stat.S_ISREG(info.st_mode):
        raise UnsafePathError(f"controlled path is not a regular file: {display}")
    try:
        descriptor = os.open(name, _file_read_flags(), dir_fd=parent_fd)
    except OSError as exc:
        raise UnsafePathError(
            f"cannot open controlled file without following a symlink: {display}: {exc}"
        ) from exc
    opened = os.fstat(descriptor)
    if (
        not stat.S_ISREG(opened.st_mode)
        or _stable_file_signature(opened) != _stable_file_signature(info)
    ):
        os.close(descriptor)
        raise UnsafePathError(f"controlled file changed while opening: {display}")
    return descriptor


def _open_root_fd(root: str | os.PathLike[str]) -> tuple[Path, int]:
    root_path = _absolute(root)
    anchor = Path(root_path.anchor)
    try:
        descriptor = os.open(anchor, _directory_flags())
    except OSError as exc:
        raise UnsafePathError(f"cannot open filesystem root {anchor}: {exc}") from exc
    current = anchor
    try:
        for part in root_path.parts[1:]:
            current /= part
            next_descriptor = _open_directory_entry(descriptor, part, current)
            os.close(descriptor)
            descriptor = next_descriptor
    except Exception:
        os.close(descriptor)
        raise
    return root_path, descriptor


def _check_trusted_root(root: str | os.PathLike[str]) -> Path:
    """Return an absolute real directory opened without following any component."""
    try:
        root_path, descriptor = _open_root_fd(root)
    except _MissingControlledPath as exc:
        raise UnsafePathError(f"controlled root does not exist: {_absolute(root)}") from exc
    os.close(descriptor)
    return root_path


def _lexical_candidate(
    path: str | os.PathLike[str], root: str | os.PathLike[str]
) -> tuple[Path, Path, Path]:
    root_path = _absolute(root)
    candidate = _absolute(path)
    try:
        relative = candidate.relative_to(root_path)
    except ValueError as exc:
        raise UnsafePathError(
            f"path escapes authorized root {root_path}: {candidate}"
        ) from exc
    return root_path, candidate, relative


def _relative_candidate(
    path: str | os.PathLike[str], root: str | os.PathLike[str]
) -> tuple[Path, Path, Path]:
    root_path, candidate, relative = _lexical_candidate(path, root)
    _check_trusted_root(root_path)
    return root_path, candidate, relative


def _open_parent_fd(
    path: str | os.PathLike[str],
    root: str | os.PathLike[str],
    *,
    create_parents: bool = False,
    mode: int = 0o755,
) -> tuple[Path, Path, int, str | None]:
    root_path, candidate, relative = _lexical_candidate(path, root)
    try:
        checked_root, descriptor = _open_root_fd(root_path)
    except _MissingControlledPath as exc:
        raise UnsafePathError(f"controlled root does not exist: {root_path}") from exc
    parts = relative.parts
    if not parts:
        return checked_root, candidate, descriptor, None
    current = checked_root
    try:
        for part in parts[:-1]:
            current /= part
            next_descriptor = _open_directory_entry(
                descriptor,
                part,
                current,
                create=create_parents,
                mode=mode,
            )
            os.close(descriptor)
            descriptor = next_descriptor
    except Exception:
        os.close(descriptor)
        raise
    return checked_root, candidate, descriptor, parts[-1]


def _open_directory_fd(
    path: str | os.PathLike[str],
    root: str | os.PathLike[str],
    *,
    create: bool = False,
    mode: int = 0o755,
) -> tuple[Path, int]:
    _root_path, candidate, parent_fd, leaf = _open_parent_fd(
        path, root, create_parents=create, mode=mode
    )
    if leaf is None:
        return candidate, parent_fd
    try:
        descriptor = _open_directory_entry(
            parent_fd, leaf, candidate, create=create, mode=mode
        )
    finally:
        os.close(parent_fd)
    return candidate, descriptor


def _open_regular_fd(
    path: str | os.PathLike[str], root: str | os.PathLike[str]
) -> tuple[Path, int]:
    _root_path, candidate, parent_fd, leaf = _open_parent_fd(path, root)
    if leaf is None:
        os.close(parent_fd)
        raise UnsafePathError(f"controlled path is not a regular file: {candidate}")
    try:
        descriptor = _open_regular_entry(parent_fd, leaf, candidate)
    finally:
        os.close(parent_fd)
    return candidate, descriptor


def _check_components(
    path: str | os.PathLike[str],
    root: str | os.PathLike[str],
    *,
    allow_missing_tail: bool = False,
) -> tuple[Path, os.stat_result | None]:
    _root_path, candidate, _relative = _lexical_candidate(path, root)
    parent_fd: int | None = None
    try:
        _root_path, candidate, parent_fd, leaf = _open_parent_fd(path, root)
        if leaf is None:
            return candidate, os.fstat(parent_fd)
        try:
            info = _entry_info(parent_fd, leaf, candidate)
        except _MissingControlledPath:
            if allow_missing_tail:
                return candidate, None
            raise UnsafePathError(f"required controlled path is missing: {candidate}")
        _reject_link(info, candidate)
        return candidate, info
    except _MissingControlledPath as exc:
        if allow_missing_tail:
            return candidate, None
        raise UnsafePathError(f"required controlled path is missing: {exc}") from exc
    finally:
        if parent_fd is not None:
            os.close(parent_fd)


def require_directory(
    path: str | os.PathLike[str], root: str | os.PathLike[str]
) -> Path:
    try:
        candidate, descriptor = _open_directory_fd(path, root)
    except _MissingControlledPath as exc:
        raise UnsafePathError(f"required controlled path is missing: {exc}") from exc
    os.close(descriptor)
    return candidate


def require_regular_file(
    path: str | os.PathLike[str], root: str | os.PathLike[str]
) -> Path:
    try:
        candidate, descriptor = _open_regular_fd(path, root)
    except _MissingControlledPath as exc:
        raise UnsafePathError(f"required controlled path is missing: {exc}") from exc
    os.close(descriptor)
    return candidate


def regular_file_exists(
    path: str | os.PathLike[str], root: str | os.PathLike[str]
) -> bool:
    try:
        _candidate, descriptor = _open_regular_fd(path, root)
    except _MissingControlledPath:
        return False
    os.close(descriptor)
    return True


def directory_exists(
    path: str | os.PathLike[str], root: str | os.PathLike[str]
) -> bool:
    try:
        _candidate, descriptor = _open_directory_fd(path, root)
    except _MissingControlledPath:
        return False
    os.close(descriptor)
    return True


def safe_makedirs(
    path: str | os.PathLike[str],
    root: str | os.PathLike[str],
    *,
    mode: int = 0o755,
) -> Path:
    candidate, descriptor = _open_directory_fd(path, root, create=True, mode=mode)
    os.close(descriptor)
    return candidate


def _ensure_destination_entry(parent_fd: int, leaf: str, display: Path) -> None:
    try:
        info = _entry_info(parent_fd, leaf, display)
    except _MissingControlledPath:
        return
    _reject_link(info, display, destination=True)
    if not stat.S_ISREG(info.st_mode):
        raise UnsafePathError(f"destination is not a regular file: {display}")


def prepare_destination(
    path: str | os.PathLike[str],
    root: str | os.PathLike[str],
    *,
    create_parents: bool = True,
) -> Path:
    try:
        _root_path, candidate, parent_fd, leaf = _open_parent_fd(
            path, root, create_parents=create_parents
        )
    except _MissingControlledPath as exc:
        raise UnsafePathError(f"required destination parent is missing: {exc}") from exc
    try:
        if leaf is None:
            raise UnsafePathError(f"destination is not a regular file: {candidate}")
        _ensure_destination_entry(parent_fd, leaf, candidate)
    finally:
        os.close(parent_fd)
    return candidate


@contextmanager
def open_regular(
    path: str | os.PathLike[str],
    root: str | os.PathLike[str],
    *,
    binary: bool = True,
    encoding: str = "utf-8",
) -> Iterator:
    try:
        candidate, descriptor = _open_regular_fd(path, root)
    except _MissingControlledPath as exc:
        raise UnsafePathError(f"required controlled path is missing: {exc}") from exc
    try:
        mode = "rb" if binary else "r"
        kwargs = {} if binary else {"encoding": encoding}
        with os.fdopen(descriptor, mode, **kwargs) as stream:
            descriptor = -1
            initial = os.fstat(stream.fileno())
            yield stream
            final = os.fstat(stream.fileno())
            if _stable_file_signature(final) != _stable_file_signature(initial):
                raise UnsafePathError(
                    f"controlled file changed while being read: {candidate}"
                )
    finally:
        if descriptor >= 0:
            os.close(descriptor)


def read_text(
    path: str | os.PathLike[str],
    root: str | os.PathLike[str],
    *,
    encoding: str = "utf-8",
    errors: str = "strict",
) -> str:
    with open_regular(path, root, binary=True) as stream:
        return stream.read().decode(encoding, errors=errors)


def digest_file(
    path: str | os.PathLike[str], root: str | os.PathLike[str], algorithm: str
) -> str:
    digest = hashlib.new(algorithm)
    with open_regular(path, root, binary=True) as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def safe_stat(
    path: str | os.PathLike[str], root: str | os.PathLike[str]
) -> os.stat_result:
    try:
        _candidate, descriptor = _open_regular_fd(path, root)
    except _MissingControlledPath as exc:
        raise UnsafePathError(f"required controlled path is missing: {exc}") from exc
    try:
        return os.fstat(descriptor)
    finally:
        os.close(descriptor)


def _create_temporary_at(parent_fd: int) -> tuple[int, str]:
    flags = (
        os.O_WRONLY
        | os.O_CREAT
        | os.O_EXCL
        | os.O_NOFOLLOW
        | getattr(os, "O_CLOEXEC", 0)
    )
    for _attempt in range(128):
        name = f".tropic-{secrets.token_hex(12)}.tmp"
        try:
            return os.open(name, flags, 0o600, dir_fd=parent_fd), name
        except FileExistsError:
            continue
        except OSError as exc:
            raise UnsafePathError(f"cannot create controlled temporary file: {exc}") from exc
    raise UnsafePathError("cannot allocate a unique controlled temporary file")


def _atomic_at(
    parent_fd: int,
    leaf: str,
    display: Path,
    writer,
    *,
    mode: int,
    timestamps: tuple[int, int] | None = None,
) -> None:
    _ensure_destination_entry(parent_fd, leaf, display)
    descriptor, temporary_name = _create_temporary_at(parent_fd)
    temporary_exists = True
    try:
        with os.fdopen(descriptor, "wb") as stream:
            descriptor = -1
            writer(stream)
            stream.flush()
            os.fsync(stream.fileno())
            os.fchmod(stream.fileno(), mode)
            if timestamps is not None:
                os.utime(stream.fileno(), ns=timestamps)
        try:
            os.replace(
                temporary_name,
                leaf,
                src_dir_fd=parent_fd,
                dst_dir_fd=parent_fd,
            )
        except OSError as exc:
            raise UnsafePathError(f"cannot atomically replace {display}: {exc}") from exc
        temporary_exists = False
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        if temporary_exists:
            try:
                os.unlink(temporary_name, dir_fd=parent_fd)
            except FileNotFoundError:
                pass


def _atomic_target(
    path: str | os.PathLike[str],
    root: str | os.PathLike[str],
    writer,
    *,
    mode: int,
    timestamps: tuple[int, int] | None = None,
) -> Path:
    _root_path, target, parent_fd, leaf = _open_parent_fd(
        path, root, create_parents=True
    )
    try:
        if leaf is None:
            raise UnsafePathError(f"destination is not a regular file: {target}")
        _atomic_at(
            parent_fd,
            leaf,
            target,
            writer,
            mode=mode,
            timestamps=timestamps,
        )
    finally:
        os.close(parent_fd)
    return target


def atomic_write_bytes(
    path: str | os.PathLike[str],
    data: bytes,
    root: str | os.PathLike[str],
    *,
    mode: int = 0o644,
) -> Path:
    return _atomic_target(path, root, lambda stream: stream.write(data), mode=mode)


def atomic_write_text(
    path: str | os.PathLike[str],
    text: str,
    root: str | os.PathLike[str],
    *,
    encoding: str = "utf-8",
    mode: int = 0o644,
) -> Path:
    return atomic_write_bytes(path, text.encode(encoding), root, mode=mode)


def atomic_write_json(
    path: str | os.PathLike[str],
    payload,
    root: str | os.PathLike[str],
    *,
    mode: int = 0o600,
) -> Path:
    text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    return atomic_write_text(path, text, root, mode=mode)


def safe_copy_file(
    source: str | os.PathLike[str],
    destination: str | os.PathLike[str],
    *,
    source_root: str | os.PathLike[str],
    destination_root: str | os.PathLike[str],
    mode: int | None = None,
) -> Path:
    with open_regular(source, source_root, binary=True) as source_stream:
        source_info = os.fstat(source_stream.fileno())
        target_mode = mode if mode is not None else stat.S_IMODE(source_info.st_mode)

        def writer(destination_stream) -> None:
            shutil.copyfileobj(source_stream, destination_stream, length=1 << 20)
            final_source_info = os.fstat(source_stream.fileno())
            if _stable_file_signature(final_source_info) != _stable_file_signature(
                source_info
            ):
                raise UnsafePathError(
                    f"controlled source changed while being copied: {_absolute(source)}"
                )

        return _atomic_target(
            destination,
            destination_root,
            writer,
            mode=target_mode,
            timestamps=(source_info.st_atime_ns, source_info.st_mtime_ns),
        )


def safe_chmod(
    path: str | os.PathLike[str],
    mode: int,
    root: str | os.PathLike[str],
    *,
    directory: bool = False,
) -> None:
    try:
        _candidate, descriptor = (
            _open_directory_fd(path, root)
            if directory
            else _open_regular_fd(path, root)
        )
    except _MissingControlledPath as exc:
        raise UnsafePathError(f"required controlled path is missing: {exc}") from exc
    try:
        os.fchmod(descriptor, mode)
    finally:
        os.close(descriptor)


def _list_directory(descriptor: int, display: Path) -> list[str]:
    try:
        return sorted(os.listdir(descriptor))
    except OSError as exc:
        raise UnsafePathError(f"cannot enumerate controlled directory {display}: {exc}") from exc


def _scan_tree_fd(descriptor: int, display: Path, files: list[Path]) -> None:
    for name in _list_directory(descriptor, display):
        candidate = display / name
        try:
            info = _entry_info(descriptor, name, candidate)
        except _MissingControlledPath as exc:
            raise UnsafePathError(
                f"controlled tree entry disappeared during enumeration: {candidate}"
            ) from exc
        _reject_link(info, candidate)
        if stat.S_ISDIR(info.st_mode):
            child = _open_directory_entry(descriptor, name, candidate)
            try:
                _scan_tree_fd(child, candidate, files)
            finally:
                os.close(child)
        elif stat.S_ISREG(info.st_mode):
            child = _open_regular_entry(descriptor, name, candidate)
            os.close(child)
            files.append(candidate)
        else:
            raise UnsafePathError(f"non-regular entry in controlled tree: {candidate}")


def require_tree_no_symlinks(
    path: str | os.PathLike[str], root: str | os.PathLike[str]
) -> Path:
    try:
        tree, descriptor = _open_directory_fd(path, root)
    except _MissingControlledPath as exc:
        raise UnsafePathError(f"required controlled path is missing: {exc}") from exc
    try:
        _scan_tree_fd(descriptor, tree, [])
    finally:
        os.close(descriptor)
    return tree


def _remove_tree_contents(descriptor: int, display: Path) -> None:
    for name in _list_directory(descriptor, display):
        candidate = display / name
        try:
            info = _entry_info(descriptor, name, candidate)
        except _MissingControlledPath as exc:
            raise UnsafePathError(
                f"controlled tree entry disappeared during removal: {candidate}"
            ) from exc
        _reject_link(info, candidate)
        if stat.S_ISDIR(info.st_mode):
            child = _open_directory_entry(descriptor, name, candidate)
            try:
                _remove_tree_contents(child, candidate)
            finally:
                os.close(child)
            try:
                os.rmdir(name, dir_fd=descriptor)
            except OSError as exc:
                raise UnsafePathError(f"cannot remove controlled directory {candidate}: {exc}") from exc
        elif stat.S_ISREG(info.st_mode):
            try:
                os.unlink(name, dir_fd=descriptor)
            except OSError as exc:
                raise UnsafePathError(f"cannot remove controlled file {candidate}: {exc}") from exc
        else:
            raise UnsafePathError(f"non-regular entry in controlled tree: {candidate}")


def safe_rmtree(
    path: str | os.PathLike[str], root: str | os.PathLike[str]
) -> None:
    root_path, candidate, relative = _lexical_candidate(path, root)
    if not relative.parts:
        raise UnsafePathError("refusing to recursively remove the authorized root itself")
    try:
        _checked_root, _candidate, parent_fd, leaf = _open_parent_fd(candidate, root_path)
    except _MissingControlledPath:
        return
    assert leaf is not None
    try:
        try:
            info = _entry_info(parent_fd, leaf, candidate)
        except _MissingControlledPath:
            return
        _reject_link(info, candidate)
        if not stat.S_ISDIR(info.st_mode):
            raise UnsafePathError(f"controlled path is not a directory: {candidate}")
        tree_fd = _open_directory_entry(parent_fd, leaf, candidate)
        try:
            # Complete validation precedes the first destructive operation.
            _scan_tree_fd(tree_fd, candidate, [])
            _remove_tree_contents(tree_fd, candidate)
        finally:
            os.close(tree_fd)
        try:
            os.rmdir(leaf, dir_fd=parent_fd)
        except OSError as exc:
            raise UnsafePathError(f"cannot remove controlled directory {candidate}: {exc}") from exc
    finally:
        os.close(parent_fd)


def safe_unlink(
    path: str | os.PathLike[str], root: str | os.PathLike[str]
) -> None:
    try:
        _root_path, candidate, parent_fd, leaf = _open_parent_fd(path, root)
    except _MissingControlledPath as exc:
        raise UnsafePathError(f"required controlled path is missing: {exc}") from exc
    if leaf is None:
        os.close(parent_fd)
        raise UnsafePathError(f"controlled path is not a regular file: {candidate}")
    try:
        try:
            descriptor = _open_regular_entry(parent_fd, leaf, candidate)
        except _MissingControlledPath as exc:
            raise UnsafePathError(f"required controlled path is missing: {candidate}") from exc
        os.close(descriptor)
        try:
            os.unlink(leaf, dir_fd=parent_fd)
        except OSError as exc:
            raise UnsafePathError(f"cannot remove controlled file {candidate}: {exc}") from exc
    finally:
        os.close(parent_fd)


def _copy_tree_contents(
    source_fd: int,
    source_display: Path,
    destination_fd: int,
    destination_display: Path,
    ignore,
) -> None:
    names = _list_directory(source_fd, source_display)
    ignored = set(ignore(os.fspath(source_display), names) or []) if ignore else set()
    for name in names:
        if name in ignored:
            continue
        source_path = source_display / name
        destination_path = destination_display / name
        try:
            info = _entry_info(source_fd, name, source_path)
        except _MissingControlledPath as exc:
            raise UnsafePathError(
                f"copytree source entry disappeared: {source_path}"
            ) from exc
        _reject_link(info, source_path)
        if stat.S_ISDIR(info.st_mode):
            source_child = _open_directory_entry(source_fd, name, source_path)
            try:
                try:
                    os.mkdir(
                        name,
                        mode=stat.S_IMODE(info.st_mode),
                        dir_fd=destination_fd,
                    )
                except OSError as exc:
                    raise UnsafePathError(
                        f"cannot create copytree directory {destination_path}: {exc}"
                    ) from exc
                destination_child = _open_directory_entry(
                    destination_fd, name, destination_path
                )
                try:
                    _copy_tree_contents(
                        source_child,
                        source_path,
                        destination_child,
                        destination_path,
                        ignore,
                    )
                    os.fchmod(destination_child, stat.S_IMODE(info.st_mode))
                    os.utime(
                        destination_child,
                        ns=(info.st_atime_ns, info.st_mtime_ns),
                    )
                finally:
                    os.close(destination_child)
            finally:
                os.close(source_child)
        elif stat.S_ISREG(info.st_mode):
            source_file = _open_regular_entry(source_fd, name, source_path)
            try:
                source_info = os.fstat(source_file)

                def writer(destination_stream) -> None:
                    while True:
                        chunk = os.read(source_file, 1 << 20)
                        if not chunk:
                            break
                        destination_stream.write(chunk)

                _atomic_at(
                    destination_fd,
                    name,
                    destination_path,
                    writer,
                    mode=stat.S_IMODE(source_info.st_mode),
                    timestamps=(source_info.st_atime_ns, source_info.st_mtime_ns),
                )
            finally:
                os.close(source_file)
        else:
            raise UnsafePathError(f"non-regular entry in controlled tree: {source_path}")


def safe_copytree(
    source: str | os.PathLike[str],
    destination: str | os.PathLike[str],
    *,
    source_root: str | os.PathLike[str],
    destination_root: str | os.PathLike[str],
    ignore=None,
) -> Path:
    try:
        source_tree, source_fd = _open_directory_fd(source, source_root)
    except _MissingControlledPath as exc:
        raise UnsafePathError(f"required controlled path is missing: {exc}") from exc
    try:
        _scan_tree_fd(source_fd, source_tree, [])
        _root, target, parent_fd, leaf = _open_parent_fd(
            destination, destination_root, create_parents=True
        )
        if leaf is None:
            os.close(parent_fd)
            raise UnsafePathError("copytree destination cannot be the authorized root")
        try:
            try:
                _entry_info(parent_fd, leaf, target)
            except _MissingControlledPath:
                pass
            else:
                raise UnsafePathError(f"copytree destination already exists: {target}")
            source_info = os.fstat(source_fd)
            try:
                os.mkdir(
                    leaf,
                    mode=stat.S_IMODE(source_info.st_mode),
                    dir_fd=parent_fd,
                )
            except OSError as exc:
                raise UnsafePathError(f"cannot create copytree destination {target}: {exc}") from exc
            target_fd = _open_directory_entry(parent_fd, leaf, target)
            try:
                _copy_tree_contents(source_fd, source_tree, target_fd, target, ignore)
                os.fchmod(target_fd, stat.S_IMODE(source_info.st_mode))
                os.utime(
                    target_fd,
                    ns=(source_info.st_atime_ns, source_info.st_mtime_ns),
                )
            finally:
                os.close(target_fd)
        finally:
            os.close(parent_fd)
    finally:
        os.close(source_fd)
    return target


def walk_regular_files(root: str | os.PathLike[str]) -> list[Path]:
    try:
        root_path, descriptor = _open_directory_fd(root, root)
    except _MissingControlledPath as exc:
        raise UnsafePathError(f"required controlled path is missing: {exc}") from exc
    files: list[Path] = []
    try:
        _scan_tree_fd(descriptor, root_path, files)
    finally:
        os.close(descriptor)
    return files


def iter_regular_files(
    root: str | os.PathLike[str], pattern: str
) -> list[Path]:
    root_path = _absolute(root)
    files = walk_regular_files(root_path)
    if "/" not in pattern and os.sep not in pattern:
        return [
            path
            for path in files
            if path.parent == root_path and fnmatch.fnmatchcase(path.name, pattern)
        ]
    return [
        path
        for path in files
        if path.relative_to(root_path).match(pattern)
    ]


def canonical_posix_relative(value: str) -> str:
    if not isinstance(value, str) or not value or "\x00" in value or "\\" in value:
        raise UnsafePathError(f"invalid relative package path: {value!r}")
    parsed = PurePosixPath(value)
    if parsed.is_absolute() or any(part in {"", ".", ".."} for part in parsed.parts):
        raise UnsafePathError(f"invalid relative package path: {value!r}")
    canonical = parsed.as_posix()
    if canonical != value:
        raise UnsafePathError(f"non-canonical relative package path: {value!r}")
    return canonical


def contained_path(
    root: str | os.PathLike[str],
    relative: str,
    *,
    allow_missing: bool = False,
) -> Path:
    canonical = canonical_posix_relative(relative)
    root_path = _check_trusted_root(root)
    candidate = root_path.joinpath(*PurePosixPath(canonical).parts)
    checked, _info = _check_components(
        candidate, root_path, allow_missing_tail=allow_missing
    )
    return checked
