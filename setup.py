#!/usr/bin/env python3
from __future__ import annotations

from gzip import GzipFile
from pathlib import Path
from shutil import copyfileobj
from typing import Iterator

import setuptools


def gzip_file(source_file: str) -> str:
    # This is actually must easier from the cli: python -m gzip --best ulauncher.1
    output_file = f"{source_file}.gz"
    dst_gzip = GzipFile(filename=output_file, mode="wb", compresslevel=9)
    with open(source_file, "rb") as src_file:
        copyfileobj(src_file, dst_gzip)
    dst_gzip.close()
    return output_file


def data_files_from_path(target_path: str, source_path: str) -> Iterator[tuple[str, list[str]]]:
    # Creates a list of valid entries for data_files weird custom format
    # Recurses over the real_path and adds it's content to package_path
    def _iter(directory: Path) -> Iterator[Path]:
        for path in directory.iterdir():
            resolved = path.resolve()
            if resolved.is_dir():
                yield from _iter(path)
            if resolved.is_file():
                yield path

    start = Path.cwd() / source_path
    for p in _iter(start.absolute()):
        relative_file = p.relative_to(start)
        yield f"{target_path}/{relative_file.parent}", [f"{source_path}/{relative_file}"]


setuptools.setup(
    packages=setuptools.find_packages(exclude=["docs", "tests", "conftest.py"]),
    # These will be placed in /usr
    data_files=[
        ("share/applications", ["io.ulauncher.Ulauncher.desktop"]),
        ("share/dbus-1/services", ["io.ulauncher.Ulauncher.service"]),
        ("share/man/man1", [gzip_file("ulauncher.1")]),
        ("lib/systemd/user", ["ulauncher.service"]),
        ("share/licenses/ulauncher", ["LICENSE"]),
        # Recursively add data as share/ulauncher, then icons
        *data_files_from_path("share/ulauncher", "data"),
        *data_files_from_path("share/icons/hicolor/scalable", "data/icons/system"),
    ],
    # can also be specified in pyproject.toml as tool.setuptools.script-files,
    # but it seems to be both "discouraged" and broken
    scripts=["bin/ulauncher", "bin/ulauncher-toggle"],
)
