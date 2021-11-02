#!/usr/bin/env python3
# -*- Mode: Python; coding: utf-8; indent-tabs-mode: nil; tab-width: 4 -*-

import subprocess
import sys
from pathlib import Path
from setuptools import Command, find_packages, setup
from setuptools.command.build_py import build_py
from ulauncher import __version__

icons = {
    "app": "data/icons/system/default/ulauncher.svg",
    "indicator": "data/icons/system/default/ulauncher-indicator.svg",
    "indicator-dark": "data/icons/system/dark/ulauncher-indicator.svg",
    "indicator-light": "data/icons/system/light/ulauncher-indicator.svg"
}


def data_files_from_path(target_path, source_path):
    # Creates a list of valid entries for data_files weird custom format
    # Recurses over the real_path and adds it's content to package_path
    entries = []
    for p in Path.cwd().glob(source_path + '/**/*'):
        if p.is_file():
            relative_file = p.relative_to(Path(source_path).absolute())
            entries.append((
                f'{target_path}/{relative_file.parent}',
                [f'{source_path}/{relative_file}'])
            )
    return entries


class build_preferences(Command):
    description = "Build Ulauncher preferences (Vue.js app)"
    force = "0"
    lint = "1"
    user_options = [
        ('force=', None, 'Rebuild even if source has no modifications since last build (default: 0)'),
        ('lint=', None, 'Lint before building (default: 1)')
    ]

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        src = Path("preferences-src")
        dst = Path("data/preferences")
        force = hasattr(self, "force") and self.force == "1"
        lint = hasattr(self, "lint") and self.lint == "1"

        if not dst.is_dir() and not src.is_dir():
            raise Exception("Preferences are missing.")

        if not force and dst.is_dir() and not src.is_dir():
            print("Using pre-built Preferences.")
            return

        sourceModified = max(map(lambda p: p.stat().st_mtime, Path.cwd().glob('preferences-src/**/*')))

        if not force and dst.is_dir() and dst.stat().st_mtime > sourceModified:
            print("Detected no changes to Preferences since last build.")
            return

        lint = "yarn lint;" if lint else ""
        subprocess.run(["sh", "-c", f"cd preferences-src; yarn; {lint} yarn build"], check=True)


class build_wrapper(build_py):
    def run(self):
        # Build Preferences before python package build
        build_preferences.run(self)
        build_py.run(self)
        print("Overwriting the namespace package with fixed values")
        Path(self.build_lib + "/ulauncher/__init__.py").write_text("\n".join([
            "__data_directory__ = '%s/share/ulauncher'" % sys.prefix,
            "__version__ = '%s'" % __version__,
            "__is_dev__ = False"
        ]))


setup(
    packages=find_packages(exclude=["tests", "conftest.py"]),
    # These will be placed in /usr
    data_files=[
        ("share/applications", ["ulauncher.desktop"]),
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
    cmdclass={'build_py': build_wrapper, 'build_prefs': build_preferences}
)
