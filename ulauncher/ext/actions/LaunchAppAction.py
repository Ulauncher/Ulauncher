import logging

from ulauncher.helpers import force_unicode
from ulauncher.utils.desktop import read_desktop_file
from .BaseAction import BaseAction

logger = logging.getLogger(__name__)


class LaunchAppAction(BaseAction):

    def __init__(self, filename):
        self.filename = filename

    def keep_app_open(self):
        return False

    def run(self):
        app = read_desktop_file(self.filename)
        logger.info('Run application %s (%s)' % (force_unicode(app.get_name()), self.filename))
        app.launch()
