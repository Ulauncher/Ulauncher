import os
from uuid import uuid4
from time import time
from ulauncher.config import CONFIG_DIR, get_default_shortcuts
from ulauncher.util.db.KeyValueJsonDb import KeyValueJsonDb
from ulauncher.util.decorator.singleton import singleton


class ShortcutsDb(KeyValueJsonDb):

    @classmethod
    @singleton
    def get_instance(cls):
        db_path = os.path.join(CONFIG_DIR, 'shortcuts.json')
        is_first_run = not os.path.exists(db_path)
        db = cls(db_path)
        db.open()

        if is_first_run:
            db._records = get_default_shortcuts()

        db.commit()

        return db

    def commit(self):
        self.ensure_user_paths()
        super(ShortcutsDb, self).commit()

    def get_sorted_records(self):
        return [rec for rec in sorted(self.get_records().itervalues(), key=lambda rec: rec['added'])]

    def get_shortcuts(self):
        return self.get_records().itervalues()

    def put_shortcut(self, name, keyword, cmd, icon, is_default_search, id=None):
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
            # use previously added time if record with the same id exists
            "added": self._records.get(id, {"added": time()})["added"]
        }
        return id

    def ensure_user_paths(self):
        for s in self.get_shortcuts():
            s['icon'] = get_user_path(s['icon'])


def get_user_path(path):
    user_home = os.path.expanduser('~')
    if path and path.startswith(user_home):
        return path.replace(user_home, '~', 1)

    return path
