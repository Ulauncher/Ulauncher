import mock
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
