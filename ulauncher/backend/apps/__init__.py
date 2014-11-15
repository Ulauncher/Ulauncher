import threading
import logging
import sys
import os
import time
from watchdog.observers import Observer
from watchdog import events
from xdg.BaseDirectory import xdg_config_home
from AppDb import AppDb
from desktop_reader import DESKTOP_DIRS, find_apps, read_desktop_file, filter_app

__all__ = ['db', 'find', 'start_sync']

logger = logging.getLogger(__name__)
db = AppDb(os.path.join(xdg_config_home, 'ulauncher', 'applist.db'))


def find(*args, **kw):
    """
    Fuzzy search of app in DB

    :param str name: name to search for
    :param int limit: max number of results
    :param int min_score: min score for search results [0..100]
    """
    return db.find(*args, **kw)


def _add_app(app):
    """
    Add app to DB
    :param Gio.DesktopAppInfo app:
    """
    db.put({"desktop_file": app.get_filename(),
            "name": app.get_name(),
            "description": app.get_description(),
            "icon": app.get_string('Icon')})


def _is_desktop_file(src_path):
    """
    Return True if file has .desktop extension
    """
    return os.path.splitext(src_path)[1] == '.desktop'


def _remove_file(src_path):
    """
    Remove .desktop file from DB
    :param str src_path:
    """
    db.remove(src_path)


def _add_file(src_path):
    """
    Add .desktop file to DB
    """
    try:
        app = read_desktop_file(src_path)
        if filter_app(app):
            _add_app(app)
    except:
        logger.warning('Cannot add %s to DB -> %s', app.get_filename(), e)


class AppEventHandler(events.FileSystemEventHandler):
    def on_created(self, event):
        if isinstance(event, events.FileCreatedEvent) and _is_desktop_file(event.src_path):
            _add_file(event.src_path)

    def on_deleted(self, event):
        if isinstance(event, events.FileDeletedEvent) and _is_desktop_file(event.src_path):
            _remove_file(event.src_path)

    def on_modified(self, event):
        if isinstance(event, events.FileModifiedEvent) and _is_desktop_file(event.src_path):
            _add_file(event.src_path)

    def on_moved(self, event):
        if isinstance(event, events.FileMovedEvent) and _is_desktop_file(event.src_path):
            _remove_file(event.src_path)
        if isinstance(event, events.FileMovedEvent) and _is_desktop_file(event.dest_path):
            _add_file(event.dest_path)


def start_sync():
    """
    Add all known .desktop files to DB and start watchdog
    """

    map(_add_app, find_apps(DESKTOP_DIRS))

    event_handler = AppEventHandler()
    observer = Observer()
    map(lambda path: observer.schedule(event_handler, os.path.expanduser(path), recursive=False), DESKTOP_DIRS)
    observer.start()

    return observer


if __name__ == "__main__":
    observer = start_sync(*sys.argv[1:])
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
