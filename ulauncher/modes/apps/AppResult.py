from os.path import basename
from gi.repository import Gio
from ulauncher.config import PATHS
from ulauncher.utils.json_data import JsonData
from ulauncher.modes.apps.launch_app import launch_app
from ulauncher.api import SearchableResult

app_starts = JsonData.new_from_file(f"{PATHS.STATE}/app_starts.json")


class AppResult(SearchableResult):
    """
    :param Gio.DesktopAppInfo app_info:
    """
    # pylint: disable=super-init-not-called

    def __init__(self, app_info):
        self.name = app_info.get_display_name()
        self.icon = app_info.get_string('Icon')
        self.description = app_info.get_description() or app_info.get_generic_name()
        self.keywords = app_info.get_keywords()
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
        sorted_tuples = sorted(app_starts.items(), key=lambda rec: rec[1], reverse=True)
        sorted_app_ids = [tuple[0] for tuple in sorted_tuples]
        return list(filter(None, map(AppResult.from_id, sorted_app_ids)))[:limit]

    def get_searchable_fields(self):
        return [
            (self.name, 1),
            (self._executable, .8),  # command names, such as "baobab" or "nautilus"
            (self.description, .7),
            *[(k, .6) for k in self.keywords]
        ]

    def on_enter(self, _):
        starts = app_starts.get(self._app_id, 0)
        app_starts.save({self._app_id: starts + 1})
        return launch_app(self._app_id)
