import logging
from .ResultItemWidget import ResultItemWidget
from ulauncher.utils.icon_loader import get_themed_icon_by_name
from ulauncher.utils.desktop import read_desktop_file

logger = logging.getLogger(__name__)


class AppResultItemWidget(ResultItemWidget):
    """
    Each app item in the result list is an instance of this class

    It is instantiated automagically if the following is done:
        - its name is set in .ui file in class attribute
        - __gtype_name__ is set to the same class name
        - this class is be imported somewhere in the code before .ui file is built
    """

    __gtype_name__ = "AppResultItem"

    def __init__(self):
        super(AppResultItemWidget, self).__init__()
        self._default_app_icon = get_themed_icon_by_name('application-default-icon')

    def set_default_icon(self):
        self.builder.get_object('item-icon').set_from_pixbuf(self._default_app_icon)
