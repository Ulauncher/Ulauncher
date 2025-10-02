from __future__ import annotations

from gi.repository import Gio

try:
    SystemDesktopAppInfo = Gio.DesktopAppInfo
except AttributeError:
    import gi

    gi.require_version("GioUnix", "2.0")
    from gi.repository import GioUnix  # type: ignore[attr-defined]

    SystemDesktopAppInfo = GioUnix.DesktopAppInfo  # type: ignore[assignment,misc,unused-ignore]


class DesktopAppInfo:
    _app_info: Gio.DesktopAppInfo
    """
    Wrapper for Gio.DesktopAppInfo without the bork.
    """

    def __init__(self, app_info: Gio.DesktopAppInfo) -> None:
        self._app_info = app_info

    @staticmethod
    def new(app_id: str) -> DesktopAppInfo | None:
        if app_info := SystemDesktopAppInfo.new(app_id):
            return DesktopAppInfo(app_info)
        return None

    @staticmethod
    def new_from_filename(filename: str) -> DesktopAppInfo | None:
        if app_info := SystemDesktopAppInfo.new_from_filename(filename):
            return DesktopAppInfo(app_info)
        return None

    @staticmethod
    def get_all() -> list[DesktopAppInfo]:
        return [DesktopAppInfo(app_info) for app_info in SystemDesktopAppInfo.get_all()]  # type: ignore[arg-type]

    ## Methods copied from Gio.DesktopAppInfo (these work fine)

    def get_id(self) -> str | None:
        return self._app_info.get_id()

    def get_name(self) -> str:
        return self._app_info.get_name()

    def get_description(self) -> str | None:
        return self._app_info.get_description()

    def get_display_name(self) -> str:
        return self._app_info.get_display_name()

    def get_commandline(self) -> str | None:
        return self._app_info.get_commandline()

    def get_executable(self) -> str:
        return self._app_info.get_executable()

    def get_icon(self) -> Gio.Icon | None:
        return self._app_info.get_icon()

    # Borked unbound methods that we have to call via the class now to work consistently
    def get_boolean(self, name: str) -> bool:
        return SystemDesktopAppInfo.get_boolean(self._app_info, name)

    def get_string(self, name: str) -> str | None:
        return SystemDesktopAppInfo.get_string(self._app_info, name)

    def get_generic_name(self) -> str | None:
        return SystemDesktopAppInfo.get_generic_name(self._app_info)

    def get_filename(self) -> str | None:
        return SystemDesktopAppInfo.get_filename(self._app_info)

    def get_keywords(self) -> list[str]:
        return SystemDesktopAppInfo.get_keywords(self._app_info)

    def get_show_in(self) -> bool:
        return SystemDesktopAppInfo.get_show_in(self._app_info)

    def get_nodisplay(self) -> bool:
        return SystemDesktopAppInfo.get_nodisplay(self._app_info)
