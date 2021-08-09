import os
import logging
from time import time, sleep
from functools import wraps
from typing import Dict

import pyinotify

from ulauncher.utils.decorator.run_async import run_async
from ulauncher.utils.desktop.reader import find_desktop_files, read_desktop_file, filter_app, find_apps_cached
from ulauncher.search.apps.AppDb import AppDb
from ulauncher.config import DESKTOP_DIRS

logger = logging.getLogger(__name__)


def _only_desktop_files(func):
    """
    Decorator for pyinotify.ProcessEvent
    Triggers event handler only for *.desktop files
    """

    @wraps(func)
    def decorator_func(self, event, *args, **kwargs):
        if os.path.splitext(event.pathname)[1] == '.desktop':
            return func(self, event, *args, **kwargs)
        return None

    return decorator_func


DeferredFiles = Dict[str, float]


class AppNotifyEventHandler(pyinotify.ProcessEvent):
    RETRY_INTERVAL = 2  # seconds
    RETRY_TIME_SPAN = (5, 30)  # make an attempt to process desktop file within 5 to 30 seconds after event came in
    # otherwise application icon or .desktop file itself may not be ready

    class InvalidDesktopFile(IOError):
        pass

    class SkipDesktopFile(Exception):
        pass

    def __init__(self, db):
        super().__init__()
        self.__db = db  # type: AppDb

        # key is a file path, value is an addition time
        self._deferred_files = {}  # type: DeferredFiles
        self._init_worker()

    @run_async(daemon=True)
    def _init_worker(self) -> None:
        """
        Add files to the DB with some delay,
        otherwise .desktop file may not be ready while application is being installed
        """
        while True:
            for pathname, start_time in list(self._deferred_files.items()):
                time_passed = time() - start_time
                if time_passed < self.RETRY_TIME_SPAN[0]:
                    # skip this file for now
                    continue

                if time_passed > self.RETRY_TIME_SPAN[1]:
                    # give up on file after time limit
                    if pathname in self._deferred_files:
                        del self._deferred_files[pathname]

                try:
                    self._add_file_sync(pathname)
                except self.InvalidDesktopFile:
                    # retry
                    pass
                except self.SkipDesktopFile:
                    # skip adding, and break the loop
                    if pathname in self._deferred_files:
                        del self._deferred_files[pathname]
                    break
                # pylint: disable=broad-except
                except Exception as e:
                    # give up on unexpected exception
                    logger.warning("Unexpected exception: %s", e)
                    if pathname in self._deferred_files:
                        del self._deferred_files[pathname]
                else:
                    # success
                    if pathname in self._deferred_files:
                        del self._deferred_files[pathname]

            sleep(self.RETRY_INTERVAL)

    def add_file_deferred(self, pathname: str) -> None:
        """
        Add .desktop file to DB a little bit later
        """
        self._deferred_files[pathname] = time()

    def _add_file_sync(self, pathname: str) -> None:
        """
        Add .desktop file to DB

        Raises self.InvalidDesktopFile if failed to add an app
        """

        # get filename of the desktop file (i.e chromium.desktop)
        file_name = os.path.basename(pathname)
        # search for desktop file in all of DESKTOP_DIRS
        pathnames_in_xdg_dirs = list(find_desktop_files(DESKTOP_DIRS, file_name))
        # if the pathname is not found in the desktop files it is overridden
        # with a file of the same name in a different XDG directory, so skip
        # trying to add this desktop file
        if pathname not in pathnames_in_xdg_dirs:
            logger.warning('Skipping adding %s to DB -> desktop file overridden in a different XDG directory', pathname)
            raise self.SkipDesktopFile(pathname)

        try:
            app = read_desktop_file(pathname)
            if filter_app(app):
                self.__db.put_app(app)
                logger.info('New app was added "%s" (%s)', app.get_name(), app.get_filename())
            else:
                raise self.InvalidDesktopFile(pathname)
        except Exception as e:
            logger.warning('Cannot add %s to DB -> %s', pathname, e)
            raise self.InvalidDesktopFile(pathname)

    def _remove_file(self, pathname: str) -> None:
        """
        Remove .desktop file from DB
        :param str pathname:
        """
        self.__db.remove_by_path(pathname)
        logger.info('App was removed (%s)', pathname)

    @_only_desktop_files
    def process_IN_CREATE(self, event):
        self.add_file_deferred(event.pathname)

    @_only_desktop_files
    def process_IN_DELETE(self, event):
        self._remove_file(event.pathname)

    @_only_desktop_files
    def process_IN_MODIFY(self, event):
        self.add_file_deferred(event.pathname)

    @_only_desktop_files
    def process_IN_MOVED_FROM(self, event):
        self._remove_file(event.pathname)

    @_only_desktop_files
    def process_IN_MOVED_TO(self, event):
        self.add_file_deferred(event.pathname)


@run_async(daemon=True)
def start():
    """
    Add all known .desktop files to the DB and start inotify watcher
    """

    db = AppDb.get_instance()
    t0 = time()
    logger.info('Started scanning desktop dirs')
    for app in find_apps_cached():
        db.put_app(app)
    logger.info('Scanned desktop dirs in %.2f seconds', (time() - t0))

    wm = pyinotify.WatchManager()
    handler = AppNotifyEventHandler(db)
    notifier = pyinotify.ThreadedNotifier(wm, handler)
    notifier.setDaemon(True)
    logger.debug('Start watching desktop files...')
    notifier.start()
    # pylint: disable=no-member
    mask = pyinotify.IN_CREATE | pyinotify.IN_DELETE | pyinotify.IN_MODIFY | \
        pyinotify.IN_MOVED_FROM | pyinotify.IN_MOVED_TO
    wm.add_watch(DESKTOP_DIRS, mask, rec=True, auto_add=True)
