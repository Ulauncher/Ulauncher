from __future__ import annotations

import logging
import os

from gi.repository import Gio, GLib

from ulauncher.utils.environment import DESKTOP_NAME

logger = logging.getLogger()
launch_command = "gapplication launch io.ulauncher.Ulauncher"


def _xfce_set_hotkey(hotkey: str):
    os.system(
        f'xfconf-query -c xfce4-keyboard-shortcuts -p "/commands/custom/{hotkey}" -n -t string -s "{launch_command}"'
    )


def _kde_set_hotkey(hotkey: str):
    kde_hotkey = hotkey.replace("<Primary>", "<Ctrl>")
    os.system(f'kwriteconfig5 --file kglobalshortcutsrc --group khotkeys --key "Ulauncher" "{launch_command}"')
    os.system(f'kwriteconfig5 --file kglobalshortcutsrc --group khotkeys --key "Ulauncher_Key" "{kde_hotkey}"')


def _gnome_set_hotkey(hotkey: str):
    base_schema = "org.gnome.settings-daemon.plugins.media-keys"
    spec_schema = f"{base_schema}.custom-keybinding"
    spec_path = f"/{spec_schema.replace('.', '/')}s/ulauncher/"

    spec = Gio.Settings.new_with_path(spec_schema, spec_path)
    spec.set_string("name", "Show Ulauncher")
    spec.set_string("command", launch_command)
    spec.set_string("binding", hotkey)

    keybindings = Gio.Settings.new(base_schema)
    enabled_keybindings = list(keybindings.get_value("custom-keybindings"))  # type: ignore[call-overload]
    if spec_path not in enabled_keybindings:
        enabled_keybindings.append(spec_path)

    keybindings.set_value("custom-keybindings", GLib.Variant("as", enabled_keybindings))


class HotkeyController:
    @staticmethod
    def is_supported():
        # User contributions to support more environments are very welcome
        return DESKTOP_NAME in ["GNOME", "XFCE"]

    @staticmethod
    def set(hotkey: str):
        if DESKTOP_NAME == "GNOME":
            _gnome_set_hotkey(hotkey)
        elif DESKTOP_NAME == "XFCE":
            _xfce_set_hotkey(hotkey)
        elif DESKTOP_NAME == "KDE":
            _kde_set_hotkey(hotkey)
        else:
            logger.warning("Ulauncher doesn't support setting hotkey for Desktop environment '%s'", DESKTOP_NAME)
