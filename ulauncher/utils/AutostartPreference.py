import os
from xdg.BaseDirectory import xdg_config_home

from ulauncher.search.apps.AppDb import AppDb
from ulauncher.utils.desktop.DesktopParser import DesktopParser


class AutostartPreference:
    AUTOSTART_FLAG = 'X-GNOME-Autostart-enabled'

    _ulauncher_desktop = None  # path to ulauncher.desktop
    _ulauncher_autostart_desktop = None  # path ~/.config/autostart/ulauncher.desktop

    def __init__(self):
        self._ulauncher_desktop = self._get_app_desktop()
        self._ulauncher_autostart_desktop = os.path.join(xdg_config_home, 'autostart', 'ulauncher.desktop')

    def _get_app_desktop(self):
        """
        :rtype: str
        :returns: path to desktop file
        """
        record = AppDb.get_instance().get_by_name('Ulauncher')
        if record:
            return record['desktop_file']

        return None

    def _get_autostart_parser(self):
        """
        Read ulauncher.desktop
        """
        return DesktopParser(self._ulauncher_autostart_desktop)

    def is_allowed(self):
        """
        :returns: True if autostart is allowed for Ulauncher
        """
        return bool(self._ulauncher_desktop)

    def is_on(self):
        """
        :returns: True if Ulauncher starts automatically
        """
        try:
            return self._get_autostart_parser().get_boolean(self.AUTOSTART_FLAG)
        # pylint: disable=broad-except
        except Exception:
            return False

    def switch(self, is_on):
        """
        if `is_on` is True, set `X-GNOME-Autostart-enabled=true` and
        write file to `~/.config/autostart/ulauncher.desktop`

        :param bool is_on:
        :raises SwitchError: if something goes wrong
        """
        if not self.is_allowed():
            raise SwitchError('Autostart is not allowed')

        try:
            try:
                autostart_info = self._get_autostart_parser()
            except IOError:
                autostart_info = DesktopParser(self._ulauncher_desktop)
                autostart_info.set_filename(self._ulauncher_autostart_desktop)

            autostart_info.set(self.AUTOSTART_FLAG, str(bool(is_on)).lower())
            autostart_info.set('Exec', '%s %s' % (autostart_info.get('Exec'), '--hide-window'))
            autostart_info.write()
        except Exception as e:
            raise SwitchError('Unexpected exception: %s' % e) from e


class SwitchError(RuntimeError):
    pass
