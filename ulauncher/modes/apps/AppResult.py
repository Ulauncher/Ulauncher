import operator
from os.path import basename
from gi.repository import Gio
from ulauncher.config import PATHS
from ulauncher.utils.json_data import JsonData
from ulauncher.modes.apps.launch_app import launch_app
from ulauncher.api.result import Result

app_starts = JsonData.new_from_file(f"{PATHS.STATE}/app_starts.json")


class AppResult(Result):
    searchable = True
    """
    :param Gio.DesktopAppInfo app_info:
    """
    # pylint: disable=super-init-not-called

    def __init__(self, app_info):
        self.name = app_info.get_display_name()
        self.icon = app_info.get_string("Icon")
        self.description = app_info.get_description() or app_info.get_generic_name()
        self.keywords = app_info.get_keywords()
        self._app_id = app_info.get_id()
        # TryExec is what we actually want (name of/path to exec), but it's often not specified
        # get_executable uses Exec, which is always specified, but it will return the actual executable.
        # Sometimes the actual executable is not the app to start, but a wrappers like "env" or "sh -c"
        self._executable = basename(app_info.get_string("TryExec") or app_info.get_executable() or "")

    @staticmethod
    def from_id(app_id):
        try:
            app_info = Gio.DesktopAppInfo.new(app_id)
            return AppResult(app_info)
        except TypeError:
            return None

    @staticmethod
    def get_top_app_ids():
        """
        Returns list of app ids sorted by launch count
        """
        sorted_tuples = sorted(app_starts.items(), key=operator.itemgetter(1), reverse=True)
        return [*map(operator.itemgetter(0), sorted_tuples)]

    @staticmethod
    def get_most_frequent(limit=5):
        """
        Returns most frequent apps

        TODO: rename to `get_most_recent` and update method to remove old apps

        :param int limit: limit
        :rtype: class:`ResultList`
        """
        return list(filter(None, map(AppResult.from_id, AppResult.get_top_app_ids())))[:limit]

    def get_searchable_fields(self):
        frequency_weight = 1
        sorted_app_ids = AppResult.get_top_app_ids()
        count = len(sorted_app_ids)
        if count:
            index = sorted_app_ids.index(self._app_id) if self._app_id in sorted_app_ids else count
            frequency_weight = 1 - (index / count * 0.1) + 0.05

        return [
            (self.name, 1 * frequency_weight),
            (self._executable, 0.8 * frequency_weight),  # command names, such as "baobab" or "nautilus"
            (self.description, 0.7 * frequency_weight),
            *[(k, 0.6 * frequency_weight) for k in self.keywords],
        ]

    def on_enter(self, _):
        starts = app_starts.get(self._app_id, 0)
        app_starts.save({self._app_id: starts + 1})
        return launch_app(self._app_id)
