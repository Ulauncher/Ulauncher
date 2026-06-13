from __future__ import annotations

import logging

from ulauncher.gi import Gio, GioUnix, GLib
from ulauncher.internals.result import Result

logger = logging.getLogger(__name__)


class OpenWithAppResult(Result):
    compact = True
    path = ""
    app_id = ""
    actions = {"open_with_app": {"name": "Open with this application", "icon": "system-run"}}


def _get_content_type(path: str) -> str:
    gfile = Gio.File.new_for_path(path)
    try:
        file_info = gfile.query_info("standard::content-type", Gio.FileQueryInfoFlags.NONE, None)
        if content_type := file_info.get_content_type():
            return content_type
    except GLib.Error:
        pass
    content_type, _ = Gio.content_type_guess(path, None)
    return content_type


def get_open_with_results(path: str) -> list[Result]:
    """Build a result for each application that can open the file at the given path."""
    results: list[Result] = []
    for app_info in Gio.AppInfo.get_recommended_for_type(_get_content_type(path)):
        app_id = app_info.get_id()
        if not app_id:
            continue
        desktop_app = GioUnix.DesktopAppInfo.new(app_id)
        results.append(
            OpenWithAppResult(
                name=app_info.get_display_name(),
                icon=(desktop_app.get_string("Icon") if desktop_app else None) or "",
                path=path,
                app_id=app_id,
            )
        )
    if not results:
        unsupported_msg = "No application is registered to handle this file type"
        return [Result(name=unsupported_msg, compact=True, icon="dialog-information")]
    return results


def open_path_with_app(app_id: str, path: str) -> None:
    app_info = GioUnix.DesktopAppInfo.new(app_id)
    if not app_info:
        logger.error("Could not load app %s to open %s", app_id, path)
        return
    uri = Gio.File.new_for_path(path).get_uri()
    try:
        app_info.launch_uris([uri])
    except GLib.Error:
        logger.exception("Could not open %s with app %s", uri, app_id)
