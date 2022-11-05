from ulauncher.config import PATHS
from ulauncher.utils.json_data import JsonData, json_data_class


@json_data_class
class Settings(JsonData):
    disable_desktop_filters = False
    clear_previous_query = True
    grab_mouse_pointer = False
    hotkey_show_app = "<Primary>space"
    jump_keys = "1234567890abcdefghijklmnopqrstuvwxyz"
    max_recent_apps = 0
    raise_if_started = False
    render_on_screen = "mouse-pointer-monitor"
    show_indicator_icon = True
    terminal_command = ""
    theme_name = "light"

    # Convert dash to underscore
    def __setitem__(self, key, value):
        super().__setitem__(key.replace("-", "_"), value)

    def get_jump_keys(self):
        # convert to list and filter out duplicates
        return list(dict.fromkeys(list(self.jump_keys)))

    @classmethod
    def load(cls):
        return cls.new_from_file(f"{PATHS.CONFIG}/settings.json")
