from __future__ import annotations

import logging
import re
import time
from shutil import which
from typing import Callable

from gi.repository import Gdk, Gtk

from ulauncher import app_id
from ulauncher.utils.environment import DESKTOP_ID, DESKTOP_NAME
from ulauncher.utils.global_shortcut_portal import GlobalShortcutsPortal
from ulauncher.utils.launch_detached import launch_detached

logger = logging.getLogger(__name__)

# How long after activation a replayed trigger key is dropped. Mutter can leave the
# shortcut's last key stuck in the activated window (mutter#4416), autorepeating until
# another key is pressed. Without a cap the key would stay swallowed for legit typing.
LEAK_SWALLOW_SECONDS = 3.0


class HotkeyController:
    """Registers the global "show Ulauncher" shortcut with the desktop environment.

    Everything goes through the GlobalShortcuts portal. The DE owns the binding and
    shows its own configuration UI; Ulauncher only requests the shortcut and reacts
    to Activated signals.
    """

    # Created lazily on the main app instance; None means binding never attempted.
    _portal: GlobalShortcutsPortal | None = None

    @staticmethod
    def is_supported() -> bool:
        """Whether a GlobalShortcuts portal backend is on the session bus."""
        from ulauncher.utils.global_shortcut_portal import is_available

        return is_available()

    @staticmethod
    def setup_default(on_activate: Callable[[], None]) -> None:
        """Bind the default global shortcut via the portal.

        The consent dialog only appears the first time (per backend); on later
        sessions the previously chosen keys are reused. Portal errors are logged,
        not raised, so Ulauncher still starts without a shortcut.
        """
        portal = HotkeyController._portal
        if portal is None:
            portal = GlobalShortcutsPortal(on_activate)
            HotkeyController._portal = portal
        elif not portal.session_handle:
            portal.on_activate = on_activate
        portal.bind()

    @staticmethod
    def show_config() -> bool:
        """Open the desktop's shortcut configuration UI for our bound shortcut."""
        if HotkeyController._portal and HotkeyController._portal.configure():
            return True
        return HotkeyController._open_de_shortcut_settings()

    @staticmethod
    def swallow_leaked_trigger(event: Gdk.EventKey) -> bool:
        """Consume key events replaying the shortcut's last key right after activation.

        Mutter can leave the last key of a shortcut stuck in XWayland windows that gain
        focus from it (mutter#4416), so it autorepeats into the prompt until another key
        is pressed. Queries never start with the trigger's character (input is
        lstripped), so dropping it is safe. Active until another key arrives, the
        swallow window expires, or the window closes.
        """
        portal = HotkeyController._portal
        if not portal or not portal.trigger_description or portal.activated_at is None:
            return False
        if time.monotonic() - portal.activated_at > LEAK_SWALLOW_SECONDS:
            portal.activated_at = None
            return False
        if event.keyval != HotkeyController.trigger_keyval():
            # Any other key ends the replay: the stuck key only repeats until then
            portal.activated_at = None
            return False
        return True

    @staticmethod
    def trigger_keyval() -> int | None:
        """Best-effort GDK keyval of the assigned trigger, parsed from the DE's text.

        Handles formats like "Press <Control><Alt>space" (GNOME, a GTK accelerator)
        and "Ctrl+Alt+Space" (KDE). Modifier words don't parse as keyvals, so the
        first matching token is the key. None when nothing parses.
        """
        portal = HotkeyController._portal
        description = portal.trigger_description if portal else None
        if not description:
            return None
        for token in reversed(description.split()):
            if keyval := Gtk.accelerator_parse(token)[0]:
                return keyval
            # KDE-style "Ctrl+Alt+Space" isn't GTK accelerator syntax; try the bare key name
            for name in reversed(token.replace("+", " ").split()):
                if keyval := Gtk.accelerator_parse(name)[0] or Gtk.accelerator_parse(name.lower())[0]:
                    return keyval
        return None

    @staticmethod
    def _open_de_shortcut_settings() -> bool:
        """Open the DE's shortcut settings, where portal-bound shortcuts are shown.

        Fallback for backends without the portal's ConfigureShortcuts (v2), which as
        of GNOME 50 / Plasma 6.7 none implement.
        """
        if DESKTOP_ID == "GNOME":
            # Portal shortcuts live on the app's page in the Applications panel (the
            # Keyboard panel doesn't list them)
            cmd = ["gnome-control-center", "applications", app_id]
        elif DESKTOP_ID == "PLASMA":
            # The shortcuts KCM is `kcm_keys`; the systemsettings binary was renamed to systemsettings5
            settings_cmd = next((alias for alias in ("systemsettings", "systemsettings5") if which(alias)), None)
            if not settings_cmd:
                logger.warning("Could not find Plasma's shortcut settings (systemsettings)")
                return False
            cmd = [settings_cmd, "kcm_keys"]
        else:
            logger.warning("Ulauncher doesn't know where '%s' configures keyboard shortcuts", DESKTOP_NAME)
            return False

        launch_detached(cmd)
        return True

    @staticmethod
    def current_trigger_label() -> str:
        """Human text of the currently assigned keys, for display in the preferences."""
        portal = HotkeyController._portal
        description = portal.trigger_description if portal else None
        if not description:
            return "Ctrl+Space"
        # The DE may prefix an instruction, e.g. GNOME returns "Press <Control>space"
        return re.sub(r"^press\s+", "", description.strip(), flags=re.IGNORECASE)

    @staticmethod
    def describe_unsupported() -> str:
        return (
            "Ulauncher couldn't set up a global shortcut: your desktop environment does not provide "
            f"the GlobalShortcuts portal (detected desktop: {DESKTOP_NAME}). "
            "Bind this command in your DE settings instead: gapplication launch io.ulauncher.Ulauncher"
        )
