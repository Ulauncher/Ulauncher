from ulauncher.modes.BaseMode import BaseMode
from ulauncher.modes.shortcuts.ShortcutsDb import ShortcutsDb
from ulauncher.modes.shortcuts.ShortcutResult import ShortcutResult


class ShortcutMode(BaseMode):

    def __init__(self):
        self.shortcutsDb = ShortcutsDb.get_instance()

    def is_enabled(self, query):
        """
        Return True if mode should be enabled for a query
        """
        return bool(self._get_active_shortcut(query))

    def _get_active_shortcut(self, query):
        for s in self.shortcutsDb.get_shortcuts():
            if query == s.get('keyword') and s.get('run_without_argument'):
                return s
            if query.startswith('%s ' % s.get('keyword')):
                return s

        return None

    def _create_items(self, shortcuts, default_search=False):
        return [ShortcutResult(default_search=default_search, **s) for s in shortcuts]

    def handle_query(self, query):
        """
        @return Action object
        """
        shortcut = self._get_active_shortcut(query)
        if not shortcut:
            raise Exception('No active shortcut. This line should not be entered')

        return [ShortcutResult(**shortcut)]

    def get_default_items(self):
        return self._create_items([s for s in self.shortcutsDb.get_shortcuts() if s['is_default_search']],
                                  default_search=True)

    def get_searchable_items(self):
        return self._create_items(self.shortcutsDb.get_shortcuts())
