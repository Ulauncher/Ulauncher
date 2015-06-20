from .WebResultItem import WebResultItem
from ulauncher.config import get_data_file


class GoogleResultItem(WebResultItem):

    def __init__(self):
        super(GoogleResultItem, self).__init__('g', 'Google', "Search Google for '{query}'",
                                               'https://google.com/search?q=%s',
                                               get_data_file('media/google-search-icon.png'))
