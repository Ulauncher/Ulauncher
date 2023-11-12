import os
import logging
from typing import List, Optional, Dict
from functools import lru_cache
from ulauncher.config import EXT_PREFERENCES_DIR
from ulauncher.utils.db.KeyValueDb import KeyValueDb
from ulauncher.utils.mypy_extensions import TypedDict
from ulauncher.api.server.ExtensionManifest import ExtensionManifest, OptionItems

logger = logging.getLogger(__name__)

PreferenceItem = TypedDict('PreferenceItem', {
    'id': str,
    'type': str,
    'name': str,
    'description': str,
    'options': OptionItems,
    'default_value': str,
    'user_value': str,
    'value': str,
})
PreferenceItems = List[PreferenceItem]


class ExtensionPreferences:
    """
    Manages extension preferences. Stores them in pickled file in cache directory
    """

    manifest = None  # type: ExtensionManifest

    @classmethod
    @lru_cache(maxsize=1000)
    def create_instance(cls, ext_id):
        return cls(ext_id, ExtensionManifest.open(ext_id))

    def __init__(self, ext_id: str, manifest: ExtensionManifest, ext_preferences_dir: str = EXT_PREFERENCES_DIR):
        self.db_path = os.path.join(ext_preferences_dir, '%s.db' % ext_id)
        self.db = KeyValueDb[str, str](self.db_path)
        self.manifest = manifest
        self._db_is_open = False

    def get_items(self, type: str = None) -> PreferenceItems:
        """
        :param str type:
        :rtype: list of dicts: [{id: .., type: .., default_value: .., user_value: ..., value: ..., description}, ...]
        """
        self._open_db()

        items = []  # type: PreferenceItems
        for p in self.manifest.get_preferences():
            if type and type != p['type']:
                continue

            default_value = p.get('default_value', '')
            items.append({
                'id': p['id'],
                'type': p['type'],
                'name': p.get('name', ''),
                'description': p.get('description', ''),
                'options': p.get('options', []),
                'default_value': default_value,
                'user_value': self.db.find(p['id']) or '',
                'value': self.db.find(p['id']) or default_value
            })

        return items

    def get_dict(self) -> Dict[str, str]:
        """
        :rtype: dict(id=value, id2=value2, ...)
        """
        items = {}
        for i in self.get_items():
            items[i['id']] = i['value']

        return items

    def get(self, id: str) -> Optional[PreferenceItem]:
        """
        Returns one item
        """
        for i in self.get_items():
            if i['id'] == id:
                return i

        return None

    def get_active_keywords(self) -> List[str]:
        """
        Filters items by type "keyword"
        """
        return [p['value'] for p in self.get_items(type='keyword') if p['value']]

    def set(self, id: str, value: str):
        """
        Updates preference

        :param str id: id as defined in manifest
        :param str value:
        """
        self.db.put(id, value)
        self.db.commit()

    def _open_db(self):
        if not self._db_is_open:
            self.db.open()
            self._db_is_open = True
