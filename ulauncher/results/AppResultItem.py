import logging
from .ResultItem import ResultItem
from ulauncher.backend.apps.icon_loader import get_themed_icon_by_name
from ulauncher.backend.apps.desktop_reader import read_desktop_file

logger = logging.getLogger(__name__)


class AppResultItem(ResultItem):
    """
    Each app item in the result list is an instance of this class

    It is instantiated automagically if the following is done:
        - its name is set in .ui file in class attribute
        - __gtype_name__ is set to the same class name
        - this class is be imported somewhere in the code before .ui file is built
    """

    __gtype_name__ = "AppResultItem"

    default_app_icon = get_themed_icon_by_name('application-default-icon')

    def set_default_icon(self):
        self.builder.get_object('item-icon').set_from_pixbuf(self.default_app_icon)

    def enter(self):
        """
        Return True if launcher window needs to be hidden
        """
        desktop_file = self.metadata['desktop_file']
        if not desktop_file:
            return

        app = read_desktop_file(desktop_file)
        logger.info('Run application %s (%s)' % (app.get_name(), desktop_file))
        return app.launch()
