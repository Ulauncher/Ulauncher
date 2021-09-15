"""
Module for detecting different states with respect to Wayland.

These functions are in a standalone module to minimize the dependencies so that
ulauncher.utils.xinit can safely use it.
"""
import os


def is_wayland():
    return os.environ.get('XDG_SESSION_TYPE', '').lower() == 'wayland'


def is_wayland_compatibility_on():
    """
    In this mode user won't be able to set app hotkey via preferences
    Set hotkey in OS Settings > Devices > Keyboard > Add Hotkey > Command: ulauncher-toggle
    GDK_BACKEND is typically unset in Wayland sessions to allow GTK apps to self-select
    """
    return is_wayland() and (gdk_backend() == '' or gdk_backend().lower().startswith('wayland'))


def gdk_backend():
    return os.environ.get('GDK_BACKEND', '')
