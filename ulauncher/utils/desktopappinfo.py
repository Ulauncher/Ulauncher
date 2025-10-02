from gi.repository import Gio

try:
    SystemDesktopAppInfo = Gio.DesktopAppInfo
except AttributeError:
    import gi

    try:
        gi.require_version("GioUnix", "2.0")
        from gi.repository import GioUnix  # type: ignore[attr-defined]

        SystemDesktopAppInfo = GioUnix.DesktopAppInfo  # type: ignore[assignment,misc,unused-ignore]
    except (ImportError, ValueError, AttributeError):
        raise ImportError("Could not import Gio.DesktopAppInfo")


class DesktopAppInfo:
    _app_info: Gio.DesktopAppInfo
    """
    Wrapper for Gio.DesktopAppInfo because it is broken in Debian Forky/Testing
    """

    def __init__(self, app_info: Gio.DesktopAppInfo) -> None:
        self._app_info = app_info

    @staticmethod
    def new(app_id):
        app_info = SystemDesktopAppInfo.new(app_id)
        if app_info:
            return DesktopAppInfo(app_info)
        return None

    @staticmethod
    def new_from_filename(filename):
        app_info = SystemDesktopAppInfo.new_from_filename(filename)
        if app_info:
            return DesktopAppInfo(app_info)
        return None

    @staticmethod
    def get_all():
        return [DesktopAppInfo(app_info) for app_info in SystemDesktopAppInfo.get_all()]  # type: ignore[arg-type]

    ## Methods copied from Gio.DesktopAppInfo (these work fine)

    def get_id(self):
        return self._app_info.get_id()

    def get_name(self):
        return self._app_info.get_name()

    def get_description(self):
        return self._app_info.get_description()

    def get_display_name(self):
        return self._app_info.get_display_name()

    def get_commandline(self):
        return self._app_info.get_commandline()

    def get_executable(self):
        return self._app_info.get_executable()

    def get_icon(self):
        return self._app_info.get_icon()

    # Borked unbound methods that we have to call via the class now to work consistently
    def get_boolean(self, name):
        return SystemDesktopAppInfo.get_boolean(self._app_info, name)

    def get_string(self, name):
        return SystemDesktopAppInfo.get_string(self._app_info, name)

    def get_generic_name(self):
        return SystemDesktopAppInfo.get_generic_name(self._app_info)

    def get_filename(self):
        return SystemDesktopAppInfo.get_filename(self._app_info)

    def get_keywords(self):
        return SystemDesktopAppInfo.get_keywords(self._app_info)

    def get_is_hidden(self):
        return SystemDesktopAppInfo.get_is_hidden(self._app_info)

    def get_show_in(self):
        return SystemDesktopAppInfo.get_show_in(self._app_info)

    def get_nodisplay(self):
        return SystemDesktopAppInfo.get_nodisplay(self._app_info)
