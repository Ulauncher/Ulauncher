import logging
import sys
import os
import time
from watchdog.observers import Observer
from watchdog import events
from desktop_reader import DESKTOP_DIRS, find_apps, read_desktop_file, filter_app
from gi.repository import Gtk
from .AppDb import AppDb as ApplicationDb  # to be able to mock AppDb deps. in unit tests
from ulauncher_lib.helpers import run_async, get_config_dir

__all__ = ['db', 'find', 'start_sync']

logger = logging.getLogger(__name__)
db = ApplicationDb(os.path.join(get_config_dir(), 'applist.db'))


def find(*args, **kw):
    """
    Fuzzy search of app in DB

    :param str name: name to search for
    :param int limit: max number of results
    :param int min_score: min score for search results [0..100]
    """
    return db.find(*args, **kw)


class AppEventHandler(events.FileSystemEventHandler):
    def __init__(self, db):
        super(AppEventHandler, self).__init__()
        self.__db = db

    def _add_file(self, src_path):
        """
        Add .desktop file to DB
        """
        try:
            app = read_desktop_file(src_path)
            if filter_app(app):
                self.__db.put_app(app)
        except Exception as e:
            logger.warning('Cannot add %s to DB -> %s' % (src_path, e))

    def _is_desktop_file(self, src_path):
        """
        Return True if file has .desktop extension
        """
        return os.path.splitext(src_path)[1] == '.desktop'

    def _remove_file(self, src_path):
        """
        Remove .desktop file from DB
        :param str src_path:
        """
        self.__db.remove(src_path)

    def on_created(self, event):
        if isinstance(event, events.FileCreatedEvent) and self._is_desktop_file(event.src_path):
            self._add_file(event.src_path)

    def on_deleted(self, event):
        if isinstance(event, events.FileDeletedEvent) and self._is_desktop_file(event.src_path):
            self._remove_file(event.src_path)

    def on_modified(self, event):
        if isinstance(event, events.FileModifiedEvent) and self._is_desktop_file(event.src_path):
            self._add_file(event.src_path)

    def on_moved(self, event):
        if isinstance(event, events.FileMovedEvent) and self._is_desktop_file(event.src_path):
            self._remove_file(event.src_path)
        if isinstance(event, events.FileMovedEvent) and self._is_desktop_file(event.dest_path):
            self._add_file(event.dest_path)


@run_async
def start_sync():
    """
    Add all known .desktop files to the DB and start watchdog
    """

    added_apps = map(lambda app: db.put_app(app), find_apps())
    logger.info('Finished scanning directories for desktop files. Indexed %s applications' % len(added_apps))

    event_handler = AppEventHandler(db)
    observer = Observer()
    map(lambda path: observer.schedule(event_handler, path, recursive=True), DESKTOP_DIRS)
    observer.start()


if __name__ == "__main__":
    thread = start_sync(*sys.argv[1:])
    thread.join()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
