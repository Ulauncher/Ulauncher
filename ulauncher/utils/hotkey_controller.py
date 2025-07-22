from __future__ import annotations

import logging
import subprocess

from gi.repository import Gio, GLib

from ulauncher import app_id
from ulauncher.ui.windows.hotkey_dialog import HotkeyDialog
from ulauncher.utils.environment import DESKTOP_ID, DESKTOP_NAME
from ulauncher.utils.launch_detached import launch_detached
from ulauncher.utils.systemd_controller import SystemdController

logger = logging.getLogger()
launch_command = f"gapplication launch {app_id}"


IS_SUPPORTED = DESKTOP_ID in ("GNOME", "XFCE", "PLASMA")


def _set_hotkey(hotkey: str) -> None:
    if not hotkey:
        return

    if DESKTOP_ID == "GNOME":
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
    elif DESKTOP_ID == "XFCE":
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
    def is_supported() -> bool:
        return IS_SUPPORTED

    @staticmethod
    def is_plasma() -> bool:
        return DESKTOP_ID == "PLASMA"

    @staticmethod
    def show_dialog() -> None:
        if DESKTOP_ID == "PLASMA":
            launch_detached(["systemsettings5", "kcm_keys"])
        elif IS_SUPPORTED:
            _set_hotkey(HotkeyDialog().run())

    @staticmethod
    def setup_default(default_hotkey: str) -> bool:
        if DESKTOP_ID == "PLASMA":
            hotkey = "Ctrl+Space"
            config_path = ["--file", "kglobalshortcutsrc", "--group", f"{app_id}.desktop", "--key"]
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
            plasma_service_controller = SystemdController("plasma-kglobalaccel")
            if plasma_service_controller.can_start():
                plasma_service_controller.restart()
            return True
        if IS_SUPPORTED:
            _set_hotkey(default_hotkey)
            return True
        return False
