import os
import time
import pyinotify
import logging
from functools import wraps

from .FileDb import FileDb
from ulauncher.helpers import find_files
from ulauncher.utils.run_async import run_async

logger = logging.getLogger(__name__)

INCLUDE_DIRS = map(os.path.expanduser, [
    '~'
])


def _filter_files(dir, filename):
    return not (filename.startswith('.') or
                filename.endswith('~') or
                filename.startswith('#') or
                '/.' in dir)


def find_user_files(dirs=INCLUDE_DIRS):
    """
    Generates file paths
    """
    for rootdir in dirs:
        rootdir = os.path.expandvars(os.path.expanduser(rootdir))
        if not os.path.exists(rootdir):
            continue
        for path in find_files(rootdir, filter_fn=_filter_files):
            yield path


def _inotify_file_filter(func):
    """
    Decorator for pyinotify.ProcessEvent
    Filters events for hidden paths
    """

    @wraps(func)
    def decorator_func(self, event, *args, **kwargs):
        filename = os.path.basename(event.pathname)
        dir = os.path.dirname(event.pathname)
        if _filter_files(dir, filename):
            return func(self, event, *args, **kwargs)

    return decorator_func


class FileNotifyEventHandler(pyinotify.ProcessEvent):

    def __init__(self, db):
        super(FileNotifyEventHandler, self).__init__()
        self._db = db

    @_inotify_file_filter
    def process_IN_CREATE(self, event):
        self._db.put_path(event.pathname)

    @_inotify_file_filter
    def process_IN_DELETE(self, event):
        self._db.remove_path(event.pathname)

    @_inotify_file_filter
    def process_IN_MOVED_FROM(self, event):
        self._db.remove_path(event.pathname)

    @_inotify_file_filter
    def process_IN_MOVED_TO(self, event):
        self._db.put_path(event.pathname)


@run_async(daemon=True)
def start():
    db = FileDb.get_instance().open()
    _watch(db)
    _reindex(db)


def _reindex(db):
    """
    Index user files and add them to FileDb
    """
    logger.debug('Removing non-existent files...')
    for file in db.get_files():
        if not os.path.exists(file):
            db.remove_path(file)

    logger.debug('Started indexing files...')
    start_time = time.time()
    i = 0
    for path in find_user_files():
        db.put_path(path)
        i += 1

        # slowdown indexing process to not spin up user's CPU fan too much
        if i % 200 == 0:
            time.sleep(0.2)

    logger.info('Indexed %s user files in %i seconds' % (i, time.time() - start_time))

    # commit changes to a file
    db.commit()


def _watch(db):
    wm = pyinotify.WatchManager()
    handler = FileNotifyEventHandler(db)
    notifier = pyinotify.ThreadedNotifier(wm, handler)
    notifier.setDaemon(True)
    logger.debug('Start watching user files...')
    notifier.start()
    mask = pyinotify.IN_CREATE | pyinotify.IN_DELETE | pyinotify.IN_MODIFY | \
        pyinotify.IN_MOVED_FROM | pyinotify.IN_MOVED_TO
    wm.add_watch(INCLUDE_DIRS, mask, rec=True, auto_add=True)
