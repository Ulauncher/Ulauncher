from typing import Any, Dict

from ulauncher.utils.mypy_extensions import TypedDict
from ulauncher.utils.decorator.singleton import singleton
from ulauncher.utils.image_loader import get_app_icon_pixbuf
from ulauncher.search.apps.AppResultItem import AppResultItem


CachedItem = TypedDict('CachedItem', {
    'icon': Any,
    'name': str,
    'sizes': Dict[int, Any]
})


class AppIconCache:

    _icons = None  # type: Dict[str, CachedItem]

    @classmethod
    @singleton
    def get_instance(cls):
        return cls()

    def __init__(self):
        self._icons = {}

    def add_icon(self, desktop_file: str, icon: Any, name: str):
        """
        :param str desktop_file:
        :param Gio.Icon icon:
        :param str name:
        """
        self._icons[desktop_file] = {
            'icon': icon,
            'name': name,
            'sizes': {}
        }

    def get_pixbuf(self, desktop_file: str):
        """
        :param str desktop_file:
        :rtype: :class:`GtkPixbuf`
        """
        icon = self._icons.get(desktop_file)
        if not icon:
            return None

        size = AppResultItem.get_icon_size()
        try:
            return icon['sizes'][size]
        except KeyError:
            pass

        pixbuf = get_app_icon_pixbuf(icon['icon'], size, icon['name'])
        icon['sizes'][size] = pixbuf

        return pixbuf

    def remove_icon(self, desktop_file: str):
        if desktop_file in self._icons:
            del self._icons[desktop_file]
