import os
import logging
from ulauncher.config import EXT_PREFERENCES_DIR
from ulauncher.util.db.KeyValueDb import KeyValueDb

logger = logging.getLogger(__name__)


class ExtensionPreferences(object):

    def __init__(self, extension_id, manifest, ext_preferences_dir=EXT_PREFERENCES_DIR):
        self.db_path = os.path.join(ext_preferences_dir, '%s.db' % extension_id)
        self.db = KeyValueDb(self.db_path)
        self.manifest = manifest
        self._db_is_open = False

    def get_items(self, type=None):
        """
        Returns list of dicts: [{id: .., type: .., defalut_value: .., user_value: ..., value: ..., description}]
        """
        self._open_db()

        items = []
        for p in self.manifest.get_preferences():
            if type and type != p['type']:
                continue

            default_value = p.get('default_value')
            items.append({
                'id': p['id'],
                'type': p['type'],
                'name': p.get('name'),
                'description': p.get('description', ''),
                'default_value': default_value,
                'user_value': self.db.find(p['id']),
                'value': self.db.find(p['id'], default_value)
            })

        return items

    def get_dict(self):
        """
        Returns dict(id=value, id2=value2, ...)
        """
        items = {}
        for i in self.get_items():
            items[i['id']] = i['value']

        return items

    def get(self, id):
        """
        Returns one item
        """
        for i in self.get_items():
            if i['id'] == id:
                return i

    def get_active_keywords(self):
        return [p['value'] for p in self.get_items(type='keyword') if p['value']]

    def set(self, id, value):
        self.db.put(id, value)
        self.db.commit()

    def _open_db(self):
        if not self._db_is_open:
            self.db.open()
            self._db_is_open = True
