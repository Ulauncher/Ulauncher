import logging
from time import time, sleep

from ulauncher.util.decorator.run_async import run_async
from ulauncher.util.decorator.singleton import singleton
from ulauncher.util.Settings import Settings
from .ExtensionDownloader import ExtensionDownloader, ExtensionIsUpToDateError
from .extension_finder import find_extensions


logger = logging.getLogger(__name__)


class ExtensionAutoupdater(object):

    _sleep_time = 60  # sec
    _app_bein_used_check_interval = 5  # sec
    _wait_until_app_not_used = 60  # sec

    @classmethod
    @singleton
    def get_instance(cls):
        from ulauncher.ui.windows.UlauncherWindow import UlauncherWindow
        ul_window = UlauncherWindow.get_instance()
        settings = Settings.get_instance()
        ext_downloader = ExtensionDownloader.get_instance()
        return cls(ext_downloader, ul_window, settings)

    def __init__(self, ext_downloader, ul_window, settings):
        super(ExtensionAutoupdater, self).__init__()
        self.ext_downloader = ext_downloader
        self.ul_window = ul_window
        self.settings = settings

    def _update(self):
        for ext_id, ext_path in find_extensions():
            try:
                self.ext_downloader.update(ext_id)
            except ExtensionIsUpToDateError:
                pass
            except Exception as e:
                logger.exception('Could not update extension %s. %s', (ext_id, e.message))

    def is_ulauncher_being_used(self):
        return time() < self.ul_window.get_last_usage_time() + self._wait_until_app_not_used

    @run_async(daemon=True)
    def run(self):
        next_update_after = time()
        while True:
            if time() >= next_update_after:
                next_update_after = time() + self.settings.get_instance().get_property("extension-update-interval")

                while self.is_ulauncher_being_used():
                    sleep(self._app_bein_used_check_interval)

                self._update()
            else:
                sleep(self._sleep_time)
