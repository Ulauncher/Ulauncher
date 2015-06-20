from .WebResultItem import WebResultItem
from ulauncher.config import get_data_file


class StackoverflowResultItem(WebResultItem):

    def __init__(self):
        super(StackoverflowResultItem, self).__init__('so', 'Stack Overflow', "Search Stack Overflow for '{query}'",
                                                      'http://stackoverflow.com/search?q=%s',
                                                      get_data_file('media/stackoverflow-icon.svg'))
