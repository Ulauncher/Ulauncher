import logging
import os

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
    logger.setLevel(logging.INFO)

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
    Return Pixbuf instance
    """
    return GdkPixbuf.Pixbuf.new_from_file_at_size(path, size, size)


def recursive_search(rootdir='.', suffix=''):
    """
    Search files recursively in rootdir
    """
    suffix = suffix.lower()
    return [os.path.join(looproot, filename)
            for looproot, _, filenames in os.walk(rootdir)
            for filename in filenames if filename.lower().endswith(suffix)]


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

    best_score = 0
    words = string.split(' ')
    words.append(string)  # add the whole record name too
    for word in words:
        score = ratio(query, word) * 100 + extra_score

        if score > best_score:
            best_score = score

    return best_score
