from .WebResultItem import WebResultItem
from ulauncher.config import get_data_file


class WikipediaResultItem(WebResultItem):

    def __init__(self):
        super(WikipediaResultItem, self).__init__('wiki', 'Wikipedia', "Search Wikipedia for '{query}'",
                                                  'http://en.wikipedia.org/wiki/Special:Search?search=%s',
                                                  get_data_file('media/wikipedia-icon.png'))
