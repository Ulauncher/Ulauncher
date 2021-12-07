import os
from typing import Type, Optional
from ulauncher.utils.mypy_extensions import TypedDict

from ulauncher.config import CONFIG_DIR
from ulauncher.utils.db.KeyValueJsonDb import KeyValueJsonDb
from ulauncher.utils.decorator.singleton import singleton

ExtensionRecord = TypedDict('ExtensionRecord', {
    'id': str,
    'url': str,
    'updated_at': str,
    'last_commit': str,
    'last_commit_time': str
})


class ExtensionDb(KeyValueJsonDb[str, ExtensionRecord]):

    @classmethod
    @singleton
    def get_instance(cls: Type['ExtensionDb']) -> 'ExtensionDb':
        db_path = os.path.join(CONFIG_DIR, 'extensions.json')
        db = cls(db_path)
        db.open()

        return db

    def find_by_url(self, url: str) -> Optional[ExtensionRecord]:
        for ext in self.get_records().values():
            if ext['url'] == url:
                return ext

        return None
