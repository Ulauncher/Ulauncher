import logging
from ulauncher.ext.SmallResultItem import SmallResultItem
from ulauncher.ui.ResultItemWidget import ResultItemWidget
from ulauncher.utils.icon_loader import get_themed_icon_by_name
from ulauncher.utils.desktop import read_desktop_file

logger = logging.getLogger(__name__)


class SmallResultItemWidget(ResultItemWidget):
    """
    It is instantiated automagically if the following is done:
        - its name is set in .ui file in class attribute
        - __gtype_name__ is set to the same class name
        - this class is be imported somewhere in the code before .ui file is built
    """

    __gtype_name__ = "SmallResultItemWidget"

    def __init__(self):
        super(SmallResultItemWidget, self).__init__()
        self._default_app_icon = get_themed_icon_by_name('application-default-icon', SmallResultItem.ICON_SIZE)

    def set_default_icon(self):
        self.builder.get_object('item-icon').set_from_pixbuf(self._default_app_icon)
