import json

from ulauncher.config import get_data_file
from ulauncher.util.Settings import Settings
from ulauncher.util.decorator.lru_cache import lru_cache


@lru_cache()
def _read_theme(name):
    """Returns dict from data/ui/css/themes/<name>/theme.json"""
    filename = get_data_file('styles', 'themes', name, 'theme.json')
    with open(filename, 'r') as f:
        return json.load(f)


def get_theme_prop(name):
    theme_name = Settings.get_instance().get_property('theme-name')
    return _read_theme(theme_name)[name]
