import os
from uuid import uuid4
from time import time
from ulauncher.config import CONFIG_DIR, get_default_shortcuts
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
        self.ensure_user_paths()
        super().commit()

    def get_sorted_records(self):
        return [rec for rec in sorted(self.get_shortcuts(), key=lambda rec: rec['added'])]

    def get_shortcuts(self):
        for rec in self.get_records().values():
            # fix for shortcuts generated in v6 branch not working in v5
            if rec.get("icon") and not os.path.isfile(rec.get("icon")):
                legacy_path = (
                    rec.get("icon", "")
                    .replace("/icons/", "/media/")
                    .replace(".svg", "-icon.svg")
                    .replace(".png", "-icon.png")
                )
                if os.path.isfile(legacy_path):
                    rec["icon"] = legacy_path
            yield rec

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

    def ensure_user_paths(self):
        for s in self.get_shortcuts():
            s['icon'] = get_user_path(s.get('icon'))


def get_user_path(path):
    user_home = os.path.expanduser('~')
    if path and path.startswith(user_home):
        return path.replace(user_home, '~', 1)

    return path
