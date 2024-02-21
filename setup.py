#!/usr/bin/env python3

from pathlib import Path

from setuptools import find_packages, setup


def data_files_from_path(target_path, source_path):
    # Creates a list of valid entries for data_files weird custom format
    # Recurses over the real_path and adds it's content to package_path
    def _iter(directory):
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


setup(
    packages=find_packages(exclude=["docs", "tests", "conftest.py"]),
    # These will be placed in /usr
    data_files=[
        ("share/applications", ["io.ulauncher.Ulauncher.desktop"]),
        ("share/dbus-1/services", ["io.ulauncher.Ulauncher.service"]),
        ("lib/systemd/user", ["ulauncher.service"]),
        ("share/licenses/ulauncher", ["LICENSE"]),
        # Recursively add data as share/ulauncher, then icons
        *data_files_from_path("share/ulauncher", "data"),
        *data_files_from_path("share/icons/hicolor/scalable", "data/icons/system"),
    ],
)
