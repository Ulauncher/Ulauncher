#!/usr/bin/env python3
# -*- Mode: Python; coding: utf-8; indent-tabs-mode: nil; tab-width: 4 -*-

import json
import subprocess
import sys
from pathlib import Path
from shutil import rmtree, which
from setuptools import Command, find_packages, setup
from setuptools.command.build_py import build_py
from ulauncher import config, VERSION

icons = {
    "app": "data/icons/system/default/ulauncher.svg",
    "indicator": "data/icons/system/default/ulauncher-indicator.svg",
    "indicator-dark": "data/icons/system/dark/ulauncher-indicator.svg",
    "indicator-light": "data/icons/system/light/ulauncher-indicator.svg",
}


def data_files_from_path(target_path, source_path):
    # Creates a list of valid entries for data_files weird custom format
    # Recurses over the real_path and adds it's content to package_path
    entries = []
    for p in Path.cwd().glob(source_path + "/**/*"):
        if p.is_file():
            relative_file = p.relative_to(Path(source_path).absolute())
            entries.append((f"{target_path}/{relative_file.parent}", [f"{source_path}/{relative_file}"]))
    return entries


class build_preferences(Command):
    description = "Build Ulauncher preferences (Vue.js app)"
    user_options = [
        ("force", None, "Rebuild even if source has no modifications since last build"),
    ]

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        src = Path("preferences-src")
        dst = Path("data/preferences")

        if "--force" in sys.argv and dst.is_dir():
            # Need to do this in particular to avoid packaging node_modules if the user has
            # been switching between building Ulauncher v5 and v6
            rmtree(dst)

        if not src.is_dir():
            raise Exception(f"{src.resolve()} directory missing.")

        sourceModified = max(map(lambda p: p.stat().st_mtime, Path.cwd().glob("preferences-src/**/*")))

        if dst.is_dir() and dst.stat().st_mtime > sourceModified:
            print("Detected no changes to Preferences since last build.")
            return

        yarnbin = which("yarn") or which("yarnpkg")
        subprocess.run(["sh", "-c", f"cd preferences-src; {yarnbin}; {yarnbin} build"], check=True)


class build_wrapper(build_py, Command):
    user_options = [
        ("with-preferences", None, "Also build preferences (when building from git tree)"),
    ]

    def run(self):
        # Build Preferences before python package build
        if "--with-preferences" in sys.argv:
            build_preferences.run(self)

        build_py.run(self)
        print("Overwriting the namespace package with fixed values")
        Path(self.build_lib + "/ulauncher/__init__.py").write_text(
            "\n".join(
                [
                    "import gi",
                    f"gi.require_versions({json.dumps(dict(config['gi_versions']))})",
                    f"ASSETS = '{sys.prefix}/share/ulauncher'",
                    f"VERSION = '{VERSION}'",
                ]
            )
        )


setup(
    packages=find_packages(exclude=["tests", "conftest.py"]),
    # These will be placed in /usr
    data_files=[
        ("share/applications", ["io.ulauncher.Ulauncher.desktop"]),
        ("lib/systemd/user", ["ulauncher.service"]),
        ("share/doc/ulauncher", ["README.md"]),
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
    cmdclass={"build_py": build_wrapper, "build_prefs": build_preferences},
)
