import os
import pytest
from ulauncher.utils.db.KeyValueDb import KeyValueDb


class TestKeyValueDb:

    @pytest.fixture
    def db_name(self, tmpdir):
        return os.path.join(str(tmpdir), 'testdb')

    @pytest.fixture
    def db(self, db_name):
        return KeyValueDb(db_name).open()

    def test_open_raises_ioerror(self):
        """It raises IOError if 'name' is a directory"""

        with pytest.raises(IOError):
            KeyValueDb('/tmp').open()

    def test_commit(self, db_name):
        """It saves changes to disk"""

        db = KeyValueDb(db_name).open()
        db.put('hello', 123)
        db.commit()

        db = KeyValueDb(db_name).open()
        assert db.find('hello') == 123

    def test_remove(self, db):
        db.put('john', {'name': 'john', 'description': 'test', 'desktop_file': 'john.desktop', 'icon': 'icon'})
        db.put('james', {'name': 'james', 'description': 'test', 'desktop_file': 'james.desktop', 'icon': 'icon'})
        assert db.get_records().get('james')
        db.remove('james')
        assert not db.get_records().get('james')
