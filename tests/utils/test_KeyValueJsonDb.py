import os
import pytest
from ulauncher.utils.db.KeyValueJsonDb import KeyValueJsonDb


class TestKeyValueJsonDb:

    @pytest.fixture
    def db_name(self, tmpdir):
        return os.path.join(str(tmpdir), 'testdb')

    @pytest.fixture
    def db(self, db_name):
        return KeyValueJsonDb(db_name).open()

    def test_commit(self, db_name):
        """It saves changes to disk"""

        db = KeyValueJsonDb(db_name).open()
        db.put('hello', 123)
        db.commit()

        db = KeyValueJsonDb(db_name).open()
        assert db.find('hello') == 123

    def test_remove(self, db):
        db.put('john', {'name': 'john', 'description': 'test', 'app_id': 'john.desktop', 'icon': 'icon'})
        db.put('james', {'name': 'james', 'description': 'test', 'app_id': 'james.desktop', 'icon': 'icon'})
        assert db.get_records().get('james')
        db.remove('james')
        assert not db.get_records().get('james')
