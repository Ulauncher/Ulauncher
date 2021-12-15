from os.path import basename, join
import gi
gi.require_version('Gio', '2.0')
# pylint: disable=wrong-import-position
from gi.repository import Gio
from ulauncher.config import STATE_DIR
from ulauncher.utils.db.KeyValueJsonDb import KeyValueJsonDb
from ulauncher.utils.Settings import Settings
from ulauncher.utils.fuzzy_search import get_score
from ulauncher.modes.apps.launch_app import launch_app
from ulauncher.api import Result
from ulauncher.modes.QueryHistoryDb import QueryHistoryDb

settings = Settings.get_instance()
_app_starts = KeyValueJsonDb(join(STATE_DIR, 'app_starts.json')).open()


class AppResult(Result):
    """
    :param Gio.DesktopAppInfo app_info:
    """
    # pylint: disable=super-init-not-called
    def __init__(self, app_info):
        self._name = app_info.get_display_name()
        # TryExec is what we actually want (name of/path to exec), but it's often not specified
        # get_executable uses Exec, which is always specified, but it will return the actual executable.
        # Sometimes the actual executable is not the app to start, but a wrappers like "env" or "sh -c"
        self._executable = basename(
            app_info.get_string('TryExec') or
            app_info.get_executable() or
            ""
        )
        self._app_info = app_info
        self._query_history = QueryHistoryDb.get_instance()

    @staticmethod
    def from_id(app_id):
        try:
            app_info = Gio.DesktopAppInfo.new(app_id)
            return AppResult(app_info)
        except TypeError:
            return None

    @staticmethod
    def search(query, min_score=50, limit=9):
        # Cast apps to AppResult objects. Default apps to Gio.DesktopAppInfo.get_all()
        apps = [AppResult(app) for app in Gio.DesktopAppInfo.get_all()]
        sorted_apps = sorted(apps, key=lambda app: app.search_score(query), reverse=True)[:limit]
        return list(filter(lambda app: app.search_score(query) > min_score, sorted_apps))

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

    def should_show(self):
        disable_desktop_filters = settings.get_property('disable-desktop-filters')
        show_in = self._app_info.get_show_in() or disable_desktop_filters
        # Make an exception for gnome-control-center, because all the very useful specific settings
        # like "Keyboard", "Wi-Fi", "Sound" etc have NoDisplay=true
        nodisplay = self._app_info.get_nodisplay() and not self._executable == 'gnome-control-center'
        return self._name and self._executable and show_in and not nodisplay

    def search_score(self, query):
        if not self.should_show():
            return 0

        # Also use the executable name, such as "baobab" or "nautilus", but score that lower
        return max(
            get_score(query, self._name),
            get_score(query, self._executable) * .8
        )

    def get(self, property):
        return self._app_info.get_string(property)

    def get_name(self):
        return self._name

    def get_description(self, _):
        return self._app_info.get_description()

    def selected_by_default(self, query):
        """
        :param ~ulauncher.modes.Query.Query query:
        """
        return self._query_history.find(query) == self._name

    def get_icon(self):
        return self._app_info.get_string('Icon')

    def on_enter(self, query):
        self._query_history.save_query(str(query), self._name)

        app_id = self._app_info.get_id()
        count = _app_starts._records.get(app_id, 0)
        _app_starts._records[app_id] = count + 1
        _app_starts.commit()
        return launch_app(app_id)
