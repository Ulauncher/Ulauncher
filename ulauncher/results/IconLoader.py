from threading import Thread
from ulauncher_lib.ulauncherconfig import get_data_file
from gi.repository import Gtk, Gio, GdkPixbuf
from ulauncher_lib.helpers import lru_cache
import logging


icon_theme = Gtk.IconTheme.get_default()
logger = logging.getLogger(__name__)


@lru_cache(maxsize=50)
def load_image(src, size):
    """
    Return Pixbuf instance
    """
    return GdkPixbuf.Pixbuf.new_from_file_at_size(src, size, size)


def get_loading_placeholder(size):
    return load_image(get_data_file('media', 'loading.png'), size)


def load_icon(icon, size, callback):
    """
    Returns "True" if image is ready (either loaded or failed to load), "False" otherwise
    "callback" will be called once image is ready

    :param str|GdkPixbuf.Pixbuf|Gio.ThemedIcon icon:
    :param int size: width and height are equal
    :param callable callback:
    """
    is_themed_icon = False

    if isinstance(icon, GdkPixbuf.Pixbuf):
        callback(icon)
        return True

    elif isinstance(icon, Gio.ThemedIcon):
        icon = icon.get_names()[0]
        is_themed_icon = True
    elif isinstance(icon, Gio.FileIcon):
        icon = icon.get_file().get_path()

    iconLoader = IconLoader(icon, size, is_themed_icon)
    iconLoader.add_callback(callback)
    iconLoader.start()

    return iconLoader.is_ready()


class IconLoader(Thread):
    """
    Usage:

    def callback(icon):
        iconWgt.set_from_pixbuf(icon) if icon else set_default_icon(iconWgt)

    iconLoader = IconLoader('icon_name', size, is_themed_icon)
    iconLoader.add_callback(callback)
    iconLoader.start()
    """

    _loaded_icon = None
    _is_ready = False  # image is loaded
    _is_started = False  # thread is started (also, it may be already finished)

    @lru_cache(maxsize=50)
    def __new__(cls, *args, **kwargs):
        """
        Cache most recent instances of IconLoader class
        """
        return super(IconLoader, cls).__new__(cls, *args, **kwargs)

    def __init__(self, icon_src, size, is_themed_icon=False):
        super(IconLoader, self).__init__()
        self._callbacks = []
        self._icon_src = icon_src
        self._size = size
        self._is_themed_icon = is_themed_icon

    def is_ready(self):
        return self._is_ready

    def is_started(self):
        return self._is_started

    def run(self):
        self._is_started = True
        self._loaded_icon = self.get_pixbuf(self._icon_src, self._size, self._is_themed_icon)
        self._is_ready = True
        self.__run_callbacks()

    def start(self):
        if not self.is_started():
            # do not start thread more than once
            super(IconLoader, self).start()
        elif self.is_ready():
            # if thread already finished, just run callbacks
            self.__run_callbacks()

    def __run_callbacks(self):
        if self._callbacks:
            map(lambda c: c(self._loaded_icon), self._callbacks)
            self._callbacks = []

    def get_pixbuf(self, icon_src, size, is_themed_icon=False):
        if is_themed_icon:
            return self.load_themed_icon(icon_src, size)
        else:
            return load_image(icon_src, size)

    def load_themed_icon(self, icon_name, size):
        """
        :param Gio.ThemedIcon icon:
        """
        try:
            return icon_theme.lookup_icon(icon_name, size, Gtk.IconLookupFlags.FORCE_SIZE).load_icon()
        except Exception as e:
            logger.info('Could not load icon: %s' % icon_name)
            return None

    def add_callback(self, callback):
        self._callbacks.append(callback)

        if self.is_ready():
            self.__run_callbacks()
