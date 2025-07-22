from __future__ import annotations

import contextlib
import os
from typing import Iterator

from ulauncher import paths


def is_extension(ext_path: str) -> bool:
    """
    Tells whether the argument is an extension directory
    """
    expected_files = [
        "manifest.json",
        "main.py",
    ]
    return all(os.path.isfile(os.path.join(ext_path, file)) for file in expected_files)


def is_manageable(ext_path: str, user_ext_path: str = paths.USER_EXTENSIONS) -> bool:
    """
    Tells the directory is user-provided extension.
    """
    ext_path = os.path.realpath(ext_path)
    return os.path.dirname(ext_path) == user_ext_path and is_extension(ext_path)


def locate_iter(ext_id: str, ext_dirs: list[str] = paths.ALL_EXTENSIONS_DIRS) -> Iterator[str]:
    """
    Yields all existing directories for given `ext_id`
    """
    for exts_dir in ext_dirs:
        ext_path = os.path.join(exts_dir, ext_id)
        if is_extension(ext_path):
            yield os.path.realpath(ext_path)


def locate(ext_id: str, ext_dirs: list[str] = paths.ALL_EXTENSIONS_DIRS) -> str | None:
    """
    Locates (an existing) extension directory.
    """
    return next(locate_iter(ext_id, ext_dirs=ext_dirs), None)


def iterate(ext_dirs: list[str] = paths.ALL_EXTENSIONS_DIRS, duplicates: bool = False) -> Iterator[tuple[str, str]]:
    """
    Yields `(ext_id, extension_path)` tuples found in a given extensions dirs
    """
    occurrences = set()
    for ext_path in ext_dirs:
        if not os.path.exists(ext_path):
            continue
        # For some reason os.path.exists ^ doesn't skip the iteration for pytest
        with contextlib.suppress(FileNotFoundError):
            for entry in os.scandir(ext_path):
                ext_id = entry.name
                if is_extension(entry.path) and (duplicates or ext_id not in occurrences):
                    occurrences.add(ext_id)
                    yield ext_id, os.path.realpath(entry.path)
