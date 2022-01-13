from os.path import basename, join
import gi
gi.require_version('Gio', '2.0')
# pylint: disable=wrong-import-position
from gi.repository import Gio
from ulauncher.config import STATE_DIR
from ulauncher.utils.db.KeyValueJsonDb import KeyValueJsonDb
from ulauncher.utils.fuzzy_search import get_score
from ulauncher.modes.apps.launch_app import launch_app
from ulauncher.api import SearchableResult

_app_starts = KeyValueJsonDb(join(STATE_DIR, 'app_starts.json')).open()


class AppResult(SearchableResult):
    """
    :param Gio.DesktopAppInfo app_info:
    """
    # pylint: disable=super-init-not-called

    def __init__(self, app_info):
        self.name = app_info.get_display_name()
        self.icon = app_info.get_string('Icon')
        self.description = app_info.get_description()
        self._app_id = app_info.get_id()
        # TryExec is what we actually want (name of/path to exec), but it's often not specified
        # get_executable uses Exec, which is always specified, but it will return the actual executable.
        # Sometimes the actual executable is not the app to start, but a wrappers like "env" or "sh -c"
        self._executable = basename(
            app_info.get_string('TryExec') or
            app_info.get_executable() or
            ""
        )

    @staticmethod
    def from_id(app_id):
        try:
            app_info = Gio.DesktopAppInfo.new(app_id)
            return AppResult(app_info)
        except TypeError:
            return None

    @staticmethod
    def get_most_frequent(limit=5):
        """
        Returns most frequent apps

        TODO: rename to `get_most_recent` and update method to remove old apps

        :param int limit: limit
        :rtype: class:`ResultList`
        """
        sorted_tuples = sorted(_app_starts._records.items(), key=lambda rec: rec[1], reverse=True)
        sorted_app_ids = [tuple[0] for tuple in sorted_tuples]
        return list(filter(None, map(AppResult.from_id, sorted_app_ids)))[:limit]

    def search_score(self, query):
        # Also use the executable name, such as "baobab" or "nautilus", but score that lower
        return max(
            get_score(query, self.name),
            get_score(query, self._executable) * .8,
            get_score(query, self.description) * .7
        )

    def on_enter(self, _):
        count = _app_starts._records.get(self._app_id, 0)
        _app_starts._records[self._app_id] = count + 1
        _app_starts.commit()
        return launch_app(self._app_id)
