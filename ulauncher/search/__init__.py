from ulauncher.helpers import singleton
from .DefaultSearchMode import DefaultSearchMode as UlauncherSearch  # rename to avoid name collision with the module
from .file_browser.FileBrowserMode import FileBrowserMode
from .calc.CalcMode import CalcMode


class Search(object):

    @classmethod
    @singleton
    def get_instance(cls):
        return cls(UlauncherSearch(), [FileBrowserMode(), CalcMode()])

    def __init__(self, default_search_mode, search_modes):
        self.default_search_mode = default_search_mode
        self.search_modes = search_modes

    def start(self, query):
        """
        Iterate over all search modes and run first enabled. Fallback to DefaultSearchMode
        """
        self.choose_search_mode(query).on_query(query).run_all()

    def choose_search_mode(self, query):
        return next((mode for mode in self.search_modes if mode.is_enabled(query)), self.default_search_mode)

    def on_key_press_event(self, widget, event, query):
        self.choose_search_mode(query).on_key_press_event(widget, event, query)
