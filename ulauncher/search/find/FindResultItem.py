import os
import mock
from ulauncher.ui import highlight_text
from ulauncher.search.file_browser.FileBrowserResultItem import FileBrowserResultItem


class FindResultItem(FileBrowserResultItem):

    def __init__(self, path):
        """
        :param Path path:
        """
        super(FindResultItem, self).__init__(path)
        self._file_queries = mock.MagicMock()  # don't use file query DB here

    def get_name(self):
        # return user path
        return self.path.get_user_path()

    def get_name_highlighted(self, query, color):
        fname = os.path.basename(self.get_name())
        fname = highlight_text(query.get_argument(), fname,
                               open_tag='<span foreground="%s">' % color, close_tag='</span>')
        return os.path.join(os.path.dirname(self.get_name()), fname)
