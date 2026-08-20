import os
import pytest
from ulauncher.utils.db.KeyValueJsonDb import KeyValueJsonDb


class TestKeyValueJsonDb:

    @pytest.fixture
    def db_name(self, tmpdir):
        return os.path.join(str(tmpdir), 'testdb.json')

    def test_open__truncated_file__starts_empty(self, db_name):
        db = KeyValueJsonDb(db_name).open()
        db.put('hello', 123)
        db.commit()
        # dropping the last byte is what an interrupted commit leaves behind
        with open(db_name, 'r+b') as file:
            file.truncate(os.path.getsize(db_name) - 1)

        assert KeyValueJsonDb(db_name).open().get_records() == {}

    def test_open__file_holding_a_list__starts_empty(self, db_name):
        with open(db_name, 'w') as file:
            file.write('["hello"]')

        assert KeyValueJsonDb(db_name).open().get_records() == {}

    def test_open__file_that_is_not_text__starts_empty(self, db_name):
        with open(db_name, 'wb') as file:
            file.write(b'\x80\x02}q\x00.')

        assert KeyValueJsonDb(db_name).open().get_records() == {}
