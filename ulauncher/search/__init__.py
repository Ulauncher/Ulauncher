from .DefaultSearchMode import DefaultSearchMode as UlauncherSearch  # rename to avoid name collision with the module
from .file_browser.FileBrowserMode import FileBrowserMode


def discover_search_modes():
    """
    Run once at startup and
    TODO: implement plugin auto-discovery in v2
    """
    return [FileBrowserMode()]


default_search_mode = UlauncherSearch()


def start_search(query, search_modes):
    """
    Iterate over all search modes and run first enabled. Fallback to DefaultSearchMode
    """

    search_mode = default_search_mode
    for mode in search_modes:
        if mode.is_enabled(query):
            search_mode = mode
            break

    search_mode.on_query(query).run_all()
