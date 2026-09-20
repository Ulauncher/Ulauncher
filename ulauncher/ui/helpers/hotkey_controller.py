from __future__ import annotations

import logging
from shutil import which
from typing import Callable

from ulauncher.utils.environment import DESKTOP_ID, DESKTOP_NAME
from ulauncher.utils.global_shortcut_portal import GlobalShortcutsPortal
from ulauncher.utils.launch_detached import launch_detached

logger = logging.getLogger(__name__)


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
    def _open_de_shortcut_settings() -> bool:
        """Open the DE's keyboard settings app, where portal-bound shortcuts are shown.

        Fallback for backends without the portal's ConfigureShortcuts (v2), which as
        of GNOME 50 / Plasma 6.7 none implement.
        """
        if DESKTOP_ID == "GNOME":
            cmd = ["gnome-control-center", "keyboard"]
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
    def describe_unsupported() -> str:
        return (
            "Ulauncher couldn't set up a global shortcut: your desktop environment does not provide "
            f"the GlobalShortcuts portal (detected desktop: {DESKTOP_NAME}). "
            "Bind this command in your DE settings instead: gapplication launch io.ulauncher.Ulauncher"
        )
