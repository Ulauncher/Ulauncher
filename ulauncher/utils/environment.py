"""
Module for detecting the display protocol.

These constants are in a standalone module to minimize the dependencies so that
ulauncher.utils.xinit can safely use it.
"""
import os


GDK_BACKEND = os.environ.get('GDK_BACKEND', '').lower()
XDG_SESSION_TYPE = os.environ.get('XDG_SESSION_TYPE', '').lower()
IS_X11 = XDG_SESSION_TYPE == 'x11'
# This means either X11 or XWayland
IS_X11_COMPATIBLE = IS_X11 or GDK_BACKEND and GDK_BACKEND.startswith('x11')
