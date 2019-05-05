import mock
import pytest

from ulauncher.api.server.ExtensionManifest import ExtensionManifest
from ulauncher.api.server.ExtensionPreferences import ExtensionPreferences
from ulauncher.utils.db.KeyValueDb import KeyValueDb


class TestExtensionPreferences:

    @pytest.fixture(autouse=True)
    def db(self, mocker):
        Db = mocker.patch('ulauncher.api.server.ExtensionPreferences.KeyValueDb')
        Db.return_value = mock.create_autospec(KeyValueDb)

        def find(_, default=None):
            return default

        Db.return_value.find.side_effect = find
        return Db.return_value

    @pytest.fixture
    def manifest_prefs(self):
        return [
            {
                "id": "name",
                "type": "input",
                "default_value": "def",
                "description": "..."
            },
            {
                "id": "main_kw",
                "type": "keyword",
                "default_value": "ti",
            },
            {
                "id": "description",
                "type": "text",
                "description": "Write a description"
            }
        ]

    @pytest.fixture
    def manifest(self, manifest_prefs):
        manifest = mock.create_autospec(ExtensionManifest)
        manifest.get_preferences.return_value = manifest_prefs
        return manifest

    @pytest.fixture
    def prefs(self, manifest):
        return ExtensionPreferences('test_extension', manifest, '/tmp')

    def test_get_items__db_open__is_called_once(self, prefs, db):
        prefs.get_items()
        prefs.get_items()
        db.open.assert_called_once_with()

    def test_get__user_value_empty__value_is_default(self, prefs):
        item = prefs.get('name')
        assert item['value'] == 'def'

    def test_get__user_value_not_empty__value_is_user_value(self, prefs, db):
        def find(*args, **kw):
            return 'user-value'

        db.find.side_effect = find
        item = prefs.get('name')
        assert item['value'] == 'user-value'

    def test_get_active_keywords__one_keyword__is_returned(self, prefs):
        assert prefs.get_active_keywords() == ['ti']

    def test_get_dict(self, prefs):
        assert prefs.get_dict() == {
            'main_kw': 'ti',
            'name': 'def',
            'description': None
        }

    def test_set__db_put__is_called(self, prefs, db):
        prefs.set('myid', 'myvalue')
        db.put.assert_called_once_with('myid', 'myvalue')

    def test_set__db_commit__is_called(self, prefs, db):
        prefs.set('myid', 'myvalue')
        db.commit.assert_called_once_with()
