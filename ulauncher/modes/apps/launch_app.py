from __future__ import annotations

import logging
import os
import re
import shlex
import shutil
from pathlib import Path

from ulauncher.gi import GioUnix, GLib
from ulauncher.modes.apps.try_raise_app import try_raise_app
from ulauncher.utils.eventbus import EventBus
from ulauncher.utils.launch_context import get_launch_context
from ulauncher.utils.launch_detached import launch_detached
from ulauncher.utils.settings import Settings

logger = logging.getLogger(__name__)
events = EventBus()


def _get_action_exec(action_name: str, desktop_entry_path: str | None) -> str | None:
    if not desktop_entry_path:
        return None
    keyfile = GLib.KeyFile()
    try:
        keyfile.load_from_file(desktop_entry_path, GLib.KeyFileFlags.NONE)
        return keyfile.get_string(f"Desktop Action {action_name}", "Exec")
    except GLib.Error:
        return None


def get_exec(app: GioUnix.DesktopAppInfo, action_name: str | None = None) -> str | None:
    """Return the launch command for the app, or one of its actions, with field codes resolved."""
    desktop_entry_path = app.get_filename()
    exec_line = _get_action_exec(action_name, desktop_entry_path) if action_name else app.get_commandline()
    if not exec_line:
        return None
    if desktop_entry_path:
        exec_line = exec_line.replace("%k", desktop_entry_path)
    # strip field codes %f, %F, %u, %U, etc
    return re.sub(r"\%[uUfFdDnNickvm]", "", exec_line).strip()


def _load_app(desktop_entry_name: str) -> GioUnix.DesktopAppInfo | None:
    app = GioUnix.DesktopAppInfo.new(desktop_entry_name)
    if not app:
        logger.error("Could not load app %s", desktop_entry_name)
    return app


def _split_runnable_terminal_command(terminal_command: str) -> list[str] | None:
    """Split the custom terminal command into argv, or warn and return None if it can't run."""
    try:
        argv = shlex.split(terminal_command)
    except ValueError:
        argv = None
    if argv and shutil.which(argv[0]):
        return argv
    logger.warning("Terminal command %r can't run. Using the default terminal instead", terminal_command)
    events.emit(
        "app:show_notification",
        "terminal_command_unavailable",
        "Terminal not found",
        f'Could not run the terminal command "{terminal_command}", so the default terminal was used. '
        "Click here to change it in the preferences.",
        "app.show-preferences",
    )
    return None


def launch_app(desktop_entry_name: str, action_name: str | None = None) -> bool:
    app_id = Path(desktop_entry_name).stem if desktop_entry_name.endswith(".desktop") else desktop_entry_name
    settings = Settings.load()
    app = _load_app(desktop_entry_name)
    if not app:
        return False

    is_dbus = app.get_boolean("DBusActivatable")
    is_terminal = app.get_boolean("Terminal")
    terminal_argv = (
        _split_runnable_terminal_command(settings.terminal_command)
        if is_terminal and settings.terminal_command
        else None
    )
    app_exec = get_exec(app, action_name)

    if action_name is not None and (is_dbus or not app_exec or (is_terminal and terminal_argv is None)):
        # for actions where we have no command to spawn, let Gio invoke the action
        launch_context = get_launch_context()
        if os.environ.get("GDK_BACKEND") != "wayland":
            launch_context.unsetenv("GDK_BACKEND")
        app.launch_action(action_name, launch_context)
        return True
    if action_name is None and (settings.raise_if_started or app.get_boolean("SingleMainWindow")):
        app_wm_id = (app.get_string("StartupWMClass") or (Path(app_exec).name if app_exec else app_id)).lower()
        if try_raise_app(app_wm_id):
            return True

    # gapplication and gtk-launch read the desktop entry themselves, so they work without a resolved Exec
    if is_dbus:  # an action with DBus activation already returned above
        # https://wiki.gnome.org/HowDoI/DBusApplicationLaunching
        cmd = ["gapplication", "launch", app_id]
    elif is_terminal and terminal_argv is None:
        cmd = ["gtk-launch", app_id]
    elif app_exec:
        try:
            app_argv = shlex.split(app_exec)
        except ValueError:
            logger.exception("Could not parse Exec for app %s: %r", app_id, app_exec)
            return False
        cmd = [*terminal_argv, *app_argv] if terminal_argv else app_argv
    else:
        logger.error("Could not get Exec for app %s", app_id)
        return False

    logger.info("Run %s (%s) Exec %s", f"action {action_name}" if action_name else "application", app_id, cmd)
    # GLib also only asks for a startup ID when the entry opts in, since one that is never
    # completed leaves the busy cursor until it times out
    startup_notify_id = (
        get_launch_context().get_startup_notify_id(app.unwrap(), []) if app.get_boolean("StartupNotify") else None
    )
    launch_detached(cmd, app.get_string("Path"), startup_notify_id=startup_notify_id)
    return True
