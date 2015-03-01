from ulauncher_lib.ulauncherconfig import get_data_file
from . ResultItem import ResultItem
from ulauncher.backend.apps.desktop_reader import read_desktop_file


class AppResultItem(ResultItem):
    """
    Each app item in the result list is an instance of this class

    It is instantiated automagically if the following is done:
        - its name is set in .ui file in class attribute
        - __gtype_name__ is set to the same class name
        - this class is be imported somewhere in the code before .ui file is built
    """

    __gtype_name__ = "AppResultItem"
    ICON_SIZE = 40
    default_app_icon = ResultItem.load_icon(get_data_file('media', 'default_app_icon.png'))

    def set_default_icon(self):
        self.builder.get_object('item-icon').set_from_pixbuf(self.default_app_icon)

    def enter(self):
        """
        Return True if launcher window needs to be hidden

        TODO: exclude launched app logs from ulauncher output
        """
        if not self.metadata['desktop_file']:
            return

        app = read_desktop_file(self.metadata['desktop_file'])

        return app.launch()
