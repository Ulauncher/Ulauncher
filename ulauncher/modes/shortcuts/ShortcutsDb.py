from uuid import uuid4
from time import time
from pathlib import Path
from ulauncher.config import CONFIG_DIR, get_default_shortcuts
from ulauncher.utils.fold_user_path import fold_user_path
from ulauncher.utils.json_data import JsonData, json_data_class


@json_data_class
class Shortcut(JsonData):
    added = 0.0
    cmd = ""
    keyword = ""
    name = ""
    icon = ""
    id = ""
    is_default_search = False
    run_without_argument = False


class ShortcutsDb(JsonData):
    # Coerce all values to Shortcuts instead of dict and fold the icon path
    def __setitem__(self, key, value):
        if hasattr(value, "icon"):
            value.icon = fold_user_path(value.icon)
        super().__setitem__(key, Shortcut(value))

    def add(self, shortcut):
        shortcut = Shortcut(shortcut)
        if not shortcut.id:
            shortcut.id = str(uuid4())

        if not self.get(shortcut.id):
            self[shortcut.id] = {"added": time()}

        self[shortcut.id].update(shortcut)

        return shortcut.id

    @classmethod
    def load(cls):
        file_path = f"{CONFIG_DIR}/shortcuts.json"
        instance = cls.new_from_file(file_path)
        if not Path(file_path).exists():
            instance.save(get_default_shortcuts())

        return instance
