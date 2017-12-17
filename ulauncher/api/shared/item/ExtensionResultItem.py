import os
import sys

from ulauncher.api.shared.action.BaseAction import BaseAction
from ulauncher.api.shared.item.ResultItem import ResultItem
from ulauncher.util.image_loader import load_image


class ExtensionResultItem(ResultItem):
    """
    Should be used in extensions.

    Cannot be subclassed there because :func:`pickle.loads` won't work in Ulauncher app
    """

    def __init__(self, *args, **kw):
        super(ExtensionResultItem, self).__init__(*args, **kw)
        self._is_extension = True
        self.extension_path = os.path.dirname(sys.argv[0])
        if self._on_enter and not isinstance(self._on_enter, BaseAction):
            raise Exception("Incorrect type of on_enter argument")

    def get_icon(self):
        if isinstance(self._icon, basestring):
            icon_path = self._icon

            if not icon_path.startswith('/'):
                icon_path = os.path.join(self.extension_path, icon_path)

            return load_image(icon_path, self.ICON_SIZE)
        else:
            # assuming it's GtkPixbuf
            return self._icon

    def on_enter(self, query):
        return self._on_enter

    def on_alt_enter(self, query):
        return self._on_alt_enter
