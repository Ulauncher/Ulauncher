from __future__ import annotations

import logging
import subprocess
from shutil import which

from gi.repository import Gio, GLib

from ulauncher.config import APP_ID
from ulauncher.ui.windows.HotkeyDialog import HotkeyDialog
from ulauncher.utils.environment import DESKTOP_NAME
from ulauncher.utils.launch_detached import launch_detached
from ulauncher.utils.systemd_controller import SystemdController

logger = logging.getLogger()
launch_command = f"gapplication launch {APP_ID}"
plasma_service_controller = SystemdController("plasma-kglobalaccel")
IS_PLASMA = which("kwriteconfig5") and which("systemsettings5") and plasma_service_controller.is_active()
IS_SUPPORTED = "GNOME" in DESKTOP_NAME or DESKTOP_NAME in ("XFCE", "PANTHEON")


def _set_hotkey(hotkey: str):
    if not hotkey:
        return

    if DESKTOP_NAME in ("GNOME", "PANTHEON", "BUDGIE:GNOME"):
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
            logger.debug("Enabling global shortcut for Gnome")
            enabled_keybindings.append(spec_path)

        logger.debug("Saving global shortcut '%s' for Gnome", hotkey)
        keybindings.set_value("custom-keybindings", GLib.Variant("as", enabled_keybindings))
    elif DESKTOP_NAME == "XFCE":
        cmd_prefix = ["xfconf-query", "--channel", "xfce4-keyboard-shortcuts"]
        all_shortcuts = subprocess.check_output([*cmd_prefix, "--list", "--verbose"]).decode().strip().split("\n")
        # Unset existing bindings
        for shortcut in all_shortcuts:
            if shortcut.endswith(launch_command):
                prop = shortcut.split()[0]
                subprocess.run([*cmd_prefix, "--reset", "--property", prop], check=True)

        cmd = [
            *cmd_prefix,
            "--property",
            f"/commands/custom/{hotkey}",
            "--create",
            "--type",
            "string",
            "--set",
            launch_command,
        ]
        logger.debug("Executing command to add XFCE global shortcut: %s", " ".join(cmd))
        subprocess.run(cmd, check=True)
    else:
        logger.warning("Ulauncher doesn't support setting hotkey for Desktop environment '%s'", DESKTOP_NAME)


class HotkeyController:
    @staticmethod
    def is_supported():
        return IS_SUPPORTED or IS_PLASMA

    @staticmethod
    def is_plasma():
        return IS_PLASMA

    @staticmethod
    def show_dialog():
        if IS_PLASMA:
            launch_detached(["systemsettings5", "kcm_keys"])
        elif IS_SUPPORTED:
            _set_hotkey(HotkeyDialog().run())

    @staticmethod
    def setup_default(default_hotkey: str) -> bool:
        if IS_PLASMA:
            hotkey = "Ctrl+Space"
            config_path = ["--file", "kglobalshortcutsrc", "--group", f"{APP_ID}.desktop", "--key"]
            config = subprocess.check_output(["kreadconfig5", *config_path, '"_launch"'])
            # only proceed if it's not already set up (don't override user prefs)
            if config.decode().strip():
                logger.debug("Ulauncher Plasma global shortcut already created")
                return False
            if default_hotkey != "<Primary>space":
                # We don't want to convert the hotkey, so instead we just hard code it
                logger.warning("Ignoring hotkey argument %s and using default '%s'", default_hotkey, hotkey)
            logger.debug("Executing kwriteconfig5 commands to add Plasma global shortcut for '%s'", hotkey)
            subprocess.run(["kwriteconfig5", *config_path, "_k_friendly_name", "Ulauncher"], check=True)
            subprocess.run(["kwriteconfig5", *config_path, "_launch", f"{hotkey},none,Ulauncher"], check=True)
            plasma_service_controller.restart()
            return True
        if IS_SUPPORTED:
            _set_hotkey(default_hotkey)
            return True
        return False
