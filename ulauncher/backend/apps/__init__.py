import logging
import sys
import os
import time
import pyinotify
from desktop_reader import DESKTOP_DIRS, find_apps, read_desktop_file, filter_app
from gi.repository import Gtk
from .AppDb import AppDb as ApplicationDb  # to be able to mock AppDb deps. in unit tests
from ulauncher_lib.helpers import run_async
from ulauncher_lib.ulauncherconfig import CONFIG_DIR, CACHE_DIR

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


def only_desktop_files(fn):
    """
    Decorator for pyinotify.ProcessEvent
    Triggers event handler only for desktop files
    """

    def decorator_fn(self, event, *args, **kwargs):
        if os.path.splitext(event.pathname)[1] == '.desktop':
            return fn(self, event, *args, **kwargs)

    return decorator_fn


class InotifyEventHandler(pyinotify.ProcessEvent):
    def __init__(self, db):
        super(InotifyEventHandler, self).__init__()
        self.__db = db

    def _add_file(self, pathname):
        """
        Add .desktop file to DB
        """
        try:
            app = read_desktop_file(pathname)
            if filter_app(app):
                self.__db.put_app(app)
                logger.info('New app was added "%s" (%s)' % (app.get_name(), app.get_filename()))
        except Exception as e:
            logger.warning('Cannot add %s to DB -> %s' % (pathname, e))

    def _remove_file(self, pathname):
        """
        Remove .desktop file from DB
        :param str pathname:
        """
        self.__db.remove_by_path(pathname)
        logger.info('App was removed (%s)' % pathname)

    @only_desktop_files
    def process_IN_CREATE(self, event):
        self._add_file(event.pathname)

    @only_desktop_files
    def process_IN_DELETE(self, event):
        self._remove_file(event.pathname)

    @only_desktop_files
    def process_IN_MODIFY(self, event):
        self._add_file(event.pathname)

    @only_desktop_files
    def process_IN_MOVED_FROM(self, event):
        self._remove_file(event.pathname)

    @only_desktop_files
    def process_IN_MOVED_TO(self, event):
        self._add_file(event.pathname)


@run_async
def start_sync():
    """
    Add all known .desktop files to the DB and start inotify watcher
    """

    added_apps = map(lambda app: db.put_app(app), find_apps())
    logger.info('Finished scanning directories for desktop files. Indexed %s applications' % len(added_apps))

    # make sure ~/.config/ulauncher/apps exists
    apps_path = os.path.join(CONFIG_DIR, 'apps')
    if not os.path.exists(apps_path):
        os.makedirs(apps_path)

    wm = pyinotify.WatchManager()
    handler = InotifyEventHandler(db)
    notifier = pyinotify.ThreadedNotifier(wm, handler)
    notifier.setDaemon(True)
    notifier.start()
    wm.add_watch(DESKTOP_DIRS, pyinotify.ALL_EVENTS, rec=True, auto_add=True)
