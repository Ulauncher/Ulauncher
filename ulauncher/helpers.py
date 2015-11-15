import logging
import re
import os
import time
from fnmatch import fnmatch

from distutils.dir_util import mkpath
from locale import gettext as _
from gi.repository import GdkPixbuf
from Levenshtein import ratio

from .config import get_data_file, CACHE_DIR
from .utils.lru_cache import lru_cache


def get_media_file(media_file_name):
    """To get quick access to icons and stuff."""
    media_filename = get_data_file('media', '%s' % (media_file_name,))
    if not os.path.exists(media_filename):
        media_filename = None

    return "file:///" + media_filename


class NullHandler(logging.Handler):
    def emit(self, record):
        pass


def set_up_logging(opts):
    # add a handler to prevent basicConfig
    root = logging.getLogger()
    null_handler = NullHandler()
    root.addHandler(null_handler)

    formatter = logging.Formatter("%(asctime)s:%(levelname)s:%(name)s: %(funcName)s() '%(message)s'")

    logger = logging.getLogger('ulauncher')
    logger_sh = logging.StreamHandler()
    logger_sh.setFormatter(formatter)
    logger.addHandler(logger_sh)
    logger.setLevel(logging.DEBUG)  # Temporarily set DEBUG by default

    # Set the logging level to show debug messages.
    if opts.verbose:
        logger.setLevel(logging.DEBUG)
        logger.debug('logging enabled')

    # set up login to a file
    log_file = os.path.join(CACHE_DIR, 'last.log')
    if os.path.exists(log_file):
        os.remove(log_file)

    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)


def alias(alternative_function_name):
    '''see http://www.drdobbs.com/web-development/184406073#l9'''
    def decorator(function):
        '''attach alternative_function_name(s) to function'''
        if not hasattr(function, 'aliases'):
            function.aliases = []
        function.aliases.append(alternative_function_name)
        return function
    return decorator


@lru_cache(maxsize=50)
def load_image(path, size):
    """
    Returns:
        Pixbuf instance or None if new_from_file_at_size() raises
    """
    logger = logging.getLogger(__name__)
    try:
        return GdkPixbuf.Pixbuf.new_from_file_at_size(path, size, size)
    except Exception as e:
        logger.warn('Could not load image %s. E: %s' % (path, e))


def find_files(directory, pattern=None, filter_fn=None):
    """
    Search files in `directory`
    `filter_fn` takes two arguments: directory, filename. If return value is False, file will be ignored
    """
    for root, _, files in os.walk(directory):
        for basename in files:
            if (not pattern or fnmatch(basename, pattern)) and (not filter_fn or filter_fn(root, basename)):
                yield os.path.join(root, basename)

objects = {}


def singleton(fn):
    """
    Decorator function.
    Call to a decorated function always returns the same instance
    Note: it doesn't take into account args and kwargs when looks up a saved instance
    Call a decorated function with spawn=True in order to get a new instance
    """
    def wrapper(*args, **kwargs):
        if not kwargs.get('spawn') and objects.get(fn):
            return objects[fn]
        else:
            instance = fn(*args, **kwargs)
            objects[fn] = instance
            return instance

    return wrapper


def string_score(query, string):
    """
    Calculate score for each word from string separately
    and then take the best one
    """
    string = string.lower()
    if not query or not string:
        return 0

    # improve score (max. by 50%) for queries that occur in a record name:
    # formula: 50 - (<index of substr>/<name length>)
    extra_score = 0
    if query in string:
        index = string.index(query)
        extra_score += 50 - (index * 50. / len(string))

        # add extra 10% to a score, if record starts with a query
        extra_score += 10 if index == 0 else 0

    # special case: improve score for query that is a file extension name
    if query.startswith('.') and string.endswith(query):
        extra_score += 30

    best_score = 0
    words = string.split(' ')
    words.append(string)  # add the whole record name too
    for word in words:
        score = ratio(query, word) * 100 + extra_score

        if score > best_score:
            best_score = score

    return best_score

_first_cap_re = re.compile('(.)([A-Z][a-z]+)')
_all_cap_re = re.compile('([a-z0-9])([A-Z])')


def split_camel_case(text, sep='_'):
    s1 = _first_cap_re.sub(r'\1%s\2' % sep, text)
    return _all_cap_re.sub(r'\1%s\2' % sep, s1).lower()
