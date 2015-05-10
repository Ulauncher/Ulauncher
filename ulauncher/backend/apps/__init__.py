import logging
import sys
import os
import time
import pyinotify
from functools import wraps
from Queue import Queue
from threading import Event
from desktop_reader import DESKTOP_DIRS, find_apps, read_desktop_file, filter_app
from gi.repository import Gtk
from .AppDb import AppDb as ApplicationDb  # to be able to mock AppDb deps. in unit tests
from ulauncher_lib.helpers import run_async
from ulauncher_lib.ulauncherconfig import CACHE_DIR

__all__ = ['db', 'find', 'start_sync']

logger = logging.getLogger(__name__)
db = ApplicationDb(os.path.join(CACHE_DIR, 'applist.db'))


def find(*args, **kw):
    """
    Fuzzy search of app in DB

    :param str name: name to search for
    :param int limit: max number of results
    :param int min_score: min score for search results [0..100]
    """
    return db.find(*args, **kw)


def only_desktop_files(func):
    """
    Decorator for pyinotify.ProcessEvent
    Triggers event handler only for *.desktop files
    """

    @wraps(func)
    def decorator_func(self, event, *args, **kwargs):
        if os.path.splitext(event.pathname)[1] == '.desktop':
            return func(self, event, *args, **kwargs)

    return decorator_func


class InotifyEventHandler(pyinotify.ProcessEvent):
    RETRY_INTERVAL = 2  # seconds
    RETRY_TIME_SPAN = (5, 30)  # make an attempt to process desktop file within 5 to 30 seconds after event came in
    # otherwise application icon or .desktop file itself may not be ready

    class InvalidDesktopFile(IOError):
        pass

    def __init__(self, db):
        super(InotifyEventHandler, self).__init__()
        self.__db = db

        self._deferred_files = {}  # key is a file path, value is an addition time
        self._init_worker()

    @run_async(daemon=True)
    def _init_worker(self):
        """
        Add files to the DB with some delay,
        otherwise .desktop file may not be ready while application is being installed
        """
        while True:
            for pathname, start_time in self._deferred_files.items():
                time_passed = time.time() - start_time
                if time_passed < self.RETRY_TIME_SPAN[0]:
                    # skip this file for now
                    continue

                if time_passed > self.RETRY_TIME_SPAN[1]:
                    # give up on file after time limit
                    del self._deferred_files[pathname]

                try:
                    self._add_file_sync(pathname)
                except self.InvalidDesktopFile:
                    # retry
                    pass
                except Exception as e:
                    # give up on unexpected exception
                    logger.warning("Unexpected exception: %s" % e)
                    del self._deferred_files[pathname]
                else:
                    # success
                    del self._deferred_files[pathname]

            time.sleep(self.RETRY_INTERVAL)

    def add_file_deffered(self, pathname):
        """
        Add .desktop file to DB a little bit later
        """
        self._deferred_files[pathname] = time.time()

    def _add_file_sync(self, pathname):
        """
        Add .desktop file to DB

        Raises self.InvalidDesktopFile if failed to add an app
        """
        try:
            app = read_desktop_file(pathname)
            if filter_app(app):
                self.__db.put_app(app)
                logger.info('New app was added "%s" (%s)' % (app.get_name(), app.get_filename()))
            else:
                raise self.InvalidDesktopFile(pathname)
        except Exception as e:
            logger.warning('Cannot add %s to DB -> %s' % (pathname, e))
            raise self.InvalidDesktopFile(pathname)

    def _remove_file(self, pathname):
        """
        Remove .desktop file from DB
        :param str pathname:
        """
        self.__db.remove_by_path(pathname)
        logger.info('App was removed (%s)' % pathname)

    @only_desktop_files
    def process_IN_CREATE(self, event):
        self.add_file_deffered(event.pathname)

    @only_desktop_files
    def process_IN_DELETE(self, event):
        self._remove_file(event.pathname)

    @only_desktop_files
    def process_IN_MODIFY(self, event):
        self.add_file_deffered(event.pathname)

    @only_desktop_files
    def process_IN_MOVED_FROM(self, event):
        self._remove_file(event.pathname)

    @only_desktop_files
    def process_IN_MOVED_TO(self, event):
        self.add_file_deffered(event.pathname)


@run_async
def start_sync():
    """
    Add all known .desktop files to the DB and start inotify watcher
    """

    added_apps = map(lambda app: db.put_app(app), find_apps())
    logger.info('Finished scanning directories for desktop files. Indexed %s applications' % len(added_apps))

    wm = pyinotify.WatchManager()
    handler = InotifyEventHandler(db)
    notifier = pyinotify.ThreadedNotifier(wm, handler)
    notifier.setDaemon(True)
    notifier.start()
    mask = pyinotify.IN_CREATE | pyinotify.IN_DELETE | pyinotify.IN_MODIFY | \
        pyinotify.IN_MOVED_FROM | pyinotify.IN_MOVED_TO
    wm.add_watch(DESKTOP_DIRS, mask, rec=True, auto_add=True)
