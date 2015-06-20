import webbrowser
from .BaseAction import BaseAction


class OpenUrlAction(BaseAction):

    def __init__(self, url):
        self.url = url

    def run(self):
        webbrowser.open_new_tab(self.url)
