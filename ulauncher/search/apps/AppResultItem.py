from os.path import basename
import gi
gi.require_version('Gio', '2.0')
# pylint: disable=wrong-import-position
from gi.repository import Gio
from ulauncher.utils.Settings import Settings
from ulauncher.utils.fuzzy_search import get_score
from ulauncher.api.shared.action.LaunchAppAction import LaunchAppAction
from ulauncher.api.shared.item.ResultItem import ResultItem
from ulauncher.search.QueryHistoryDb import QueryHistoryDb
from ulauncher.search.apps.AppStatDb import AppStatDb
from ulauncher.utils.image_loader import get_app_icon_pixbuf

settings = Settings.get_instance()


class AppResultItem(ResultItem):
    """
    :param Gio.DesktopAppInfo app_info:
    """
    # pylint: disable=super-init-not-called
    def __init__(self, app_info):
        self._name = app_info.get_display_name()
        # TryExec is what we actually want (name of/path to exec), but it's often not specified
        # get_executable uses Exec, which is always specified, but it will return the actual executable.
        # Sometimes the actual executable is not the app to start, but a wrappers like "env" or "sh -c"
        self._executable = basename(app_info.get_string('TryExec') or app_info.get_executable())
        self._app_info = app_info
        self._query_history = QueryHistoryDb.get_instance()
        self._app_stat_db = AppStatDb.get_instance()

    @staticmethod
    def from_id(app_id):
        try:
            app_info = Gio.DesktopAppInfo.new(app_id)
            return AppResultItem(app_info)
        except TypeError:
            return None

    @staticmethod
    def search(query, min_score=50, limit=9, apps=None):
        # Cast apps to AppResultItem objects. Default apps to Gio.DesktopAppInfo.get_all()
        apps = [AppResultItem(app) for app in apps or Gio.DesktopAppInfo.get_all()]
        sorted_apps = sorted(apps, key=lambda app: app.search_score(query), reverse=True)[:limit]
        return list(filter(lambda app: app.search_score(query) > min_score, sorted_apps))

    def should_show(self):
        disable_desktop_filters = settings.get_property('disable-desktop-filters')
        blacklisted_dirs = settings.get_property('blacklisted-desktop-dirs')
        blacklisted_dirs_list = blacklisted_dirs.split(':') if blacklisted_dirs else []
        show_in = self._app_info.get_show_in() or disable_desktop_filters
        blacklisted = any(map(self._app_info.get_filename().startswith, blacklisted_dirs_list))
        # Make an exception for gnome-control-center, because all the very useful specific settings
        # like "Keyboard", "Wi-Fi", "Sound" etc have NoDisplay=true
        nodisplay = self._app_info.get_nodisplay() and not self._executable == 'gnome-control-center'
        return self._name and self._executable and show_in and not nodisplay and not blacklisted

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
        :param ~ulauncher.search.Query.Query query:
        """
        return self._query_history.find(query) == self._name

    def get_icon(self):
        return get_app_icon_pixbuf(self._app_info.get_icon(), self.get_icon_size())

    def on_enter(self, query):
        self._query_history.save_query(str(query), self._name)

        self._app_stat_db.inc_count(self._app_info.get_id())
        self._app_stat_db.commit()
        return LaunchAppAction(self._app_info.get_filename())
