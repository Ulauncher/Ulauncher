import os
import pytest

from ulauncher.api.server.ExtensionDb import ExtensionDb


class TestExtensionDb:

    @pytest.fixture
    def ext_db(self, tmpdir):
        return ExtensionDb(os.path.join(str(tmpdir), 'extensions.json')).open()

    def test_find_by_url(self, ext_db):
        ext_db.put('a', {'url': 'https://github.com/a/b'})
        expected = {'url': 'https://github.com/a/c'}
        ext_db.put('b', expected)
        ext_db.put('c', {'url': 'https://github.com/a/d'})

        assert ext_db.find_by_url('https://github.com/a/c') == expected
        assert ext_db.find_by_url('') is None
