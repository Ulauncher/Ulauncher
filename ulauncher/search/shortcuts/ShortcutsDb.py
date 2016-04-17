import os
from uuid import uuid4
from time import time
from operator import itemgetter
from ulauncher.helpers import singleton
from ulauncher.config import CONFIG_DIR
from ulauncher.utils.KeyValueDb import KeyValueDb


class ShortcutsDb(KeyValueDb):

    @classmethod
    @singleton
    def get_instance(cls):
        db = cls(os.path.join(CONFIG_DIR, 'shortcuts.db'))
        db.open()
        return db

    def get_sorted_records(self):
        return [rec for rec in sorted(self.get_records().itervalues(), key=lambda rec: rec['added'])]

    def put_shortcut(self, name, keyword, cmd, icon, id=None):
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
            # use previously added time if record with the same id exists
            "added": self._records.get(id, {"added": time()})["added"]
        }
        return id
