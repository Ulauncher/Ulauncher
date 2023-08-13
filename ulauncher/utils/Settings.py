from ulauncher.config import PATHS
from ulauncher.utils.json_conf import JsonConf

_settings_file = f"{PATHS.CONFIG}/settings.json"


class Settings(JsonConf):
    disable_desktop_filters = False
    clear_previous_query = True
    grab_mouse_pointer = False
    hotkey_show_app = ""  # Note that this is no longer used, other than for migrating to the DE wrapper
    jump_keys = "1234567890abcdefghijklmnopqrstuvwxyz"
    enable_application_mode = True
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
        return super().load(_settings_file)
