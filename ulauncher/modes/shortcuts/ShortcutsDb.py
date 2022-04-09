import os
from uuid import uuid4
from time import time
from ulauncher.config import CONFIG_DIR, get_default_shortcuts
from ulauncher.utils.fold_user_path import fold_user_path
from ulauncher.utils.db.KeyValueJsonDb import KeyValueJsonDb
from ulauncher.utils.decorator.singleton import singleton


class ShortcutsDb(KeyValueJsonDb):

    @classmethod
    @singleton
    def get_instance(cls):
        db_path = os.path.join(CONFIG_DIR, 'shortcuts.json')
        is_first_run = not os.path.exists(db_path)
        db = cls(db_path)
        db.open()

        if is_first_run:
            db.set_records(get_default_shortcuts())

        db.commit()

        return db

    def commit(self):
        for shortcut in self.get_shortcuts():
            shortcut['icon'] = fold_user_path(shortcut['icon'])
        super().commit()

    def get_shortcuts(self):
        return list(self.get_records().values())

    # pylint: disable=too-many-arguments
    def put_shortcut(self, name, keyword, cmd, icon, is_default_search, run_without_argument, id=None):
        """
        If id is not provided it will be generated using uuid4() function
        """
        id = id or str(uuid4())
        self._records[id] = {
            "id": id,
            "name": name,
            "keyword": keyword,
            "cmd": cmd,
            "icon": icon,
            "is_default_search": bool(is_default_search),
            "run_without_argument": bool(run_without_argument),
            # use previously added time if record with the same id exists
            "added": self._records.get(id, {"added": time()})["added"]
        }
        return id
