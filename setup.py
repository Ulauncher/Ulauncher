#!/usr/bin/env python3

from pathlib import Path

from setuptools import find_packages, setup

icons = {
    "app": "data/icons/system/default/ulauncher.svg",
    "indicator": "data/icons/system/default/ulauncher-indicator.svg",
    "indicator-dark": "data/icons/system/dark/ulauncher-indicator.svg",
    "indicator-light": "data/icons/system/light/ulauncher-indicator.svg",
}


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
        # Install icons in themes, so different icons can be used for different depending on theme
        # It's only needed for the app indicator icon
        ("share/icons/hicolor/48x48/apps", [icons["app"], icons["indicator"]]),
        ("share/icons/hicolor/scalable/apps", [icons["app"], icons["indicator"]]),
        # for Fedora + GNOME
        ("share/icons/gnome/scalable/apps", [icons["app"], icons["indicator"]]),
        # for Elementary
        ("share/icons/elementary/scalable/apps", [icons["indicator-light"]]),
        # for Ubuntu
        ("share/icons/breeze/apps/48", [icons["indicator-dark"]]),
        ("share/icons/ubuntu-mono-dark/scalable/apps", [icons["indicator"]]),
        ("share/icons/ubuntu-mono-light/scalable/apps", [icons["indicator-dark"]]),
        # Recursively add data as share/ulauncher
        *data_files_from_path("share/ulauncher", "data"),
    ],
)
