"""
Module for detecting the display protocol.

These constants are in a standalone module to minimize the dependencies so that
ulauncher.utils.xinit can safely use it.
"""
import os


GDK_BACKEND = os.environ.get('GDK_BACKEND', '').lower()
XDG_SESSION_TYPE = os.environ.get('XDG_SESSION_TYPE', '').lower()
IS_WAYLAND = XDG_SESSION_TYPE == 'wayland'
# This means either X11 or XWayland
IS_X11_BACKEND = not IS_WAYLAND and GDK_BACKEND and not GDK_BACKEND.startswith('wayland')
