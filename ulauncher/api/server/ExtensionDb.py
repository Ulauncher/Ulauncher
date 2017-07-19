import os
from ulauncher.config import CONFIG_DIR
from ulauncher.util.db.KeyValueJsonDb import KeyValueJsonDb
from ulauncher.util.decorator.singleton import singleton


class ExtensionDb(KeyValueJsonDb):

    @classmethod
    @singleton
    def get_instance(cls):
        db_path = os.path.join(CONFIG_DIR, 'extensions.json')
        db = cls(db_path)
        db.open()

        return db

    def find_by_url(self, url):
        for ext in self.get_records().values():
            if ext['url'] == url:
                return ext
