import logging

from ulauncher.util.desktop.reader import read_desktop_file
from ulauncher.util.string import force_unicode
from .BaseAction import BaseAction

logger = logging.getLogger(__name__)


class LaunchAppAction(BaseAction):
    """
    Launches app by given `.desktop` file path

    :param str filename: path to .desktop file
    """

    def __init__(self, filename):
        self.filename = filename

    def keep_app_open(self):
        return False

    def run(self):
        app = read_desktop_file(self.filename)
        logger.info('Run application %s (%s)' % (force_unicode(app.get_name()), self.filename))
        app.launch()
