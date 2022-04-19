"""
Module for detecting the display protocol.

These constants are in a standalone module to minimize the dependencies so that
ulauncher.utils.xinit can safely use it.
"""
import os
import csv
import pathlib


with open(pathlib.Path("/etc/os-release")) as stream:
    reader = csv.reader(stream, delimiter="=")
    os_release = dict(reader)


GDK_BACKEND = os.environ.get("GDK_BACKEND", "").upper()
XDG_SESSION_TYPE = os.environ.get("XDG_SESSION_TYPE", "").upper()
DESKTOP_NAME = os.environ.get("XDG_CURRENT_DESKTOP", "") or "Unknown Desktop"
DISTRO = os_release["PRETTY_NAME"] or "Unknown Distro"
IS_X11 = XDG_SESSION_TYPE == "X11"
# This means either X11 or XWayland
IS_X11_COMPATIBLE = IS_X11 or GDK_BACKEND and GDK_BACKEND.startswith("X11")
