import os
import pytest
import mock
from ulauncher.search.shortcuts.ShortcutsDb import ShortcutsDb


class TestShortcutsDb(object):

    @pytest.fixture(autouse=True)
    def get_default_shortcuts(self, mocker):
        default = mocker.patch('ulauncher.search.shortcuts.ShortcutsDb.get_default_shortcuts')
        default.return_value = []
        return default

    @pytest.fixture
    def db(self):
        db = ShortcutsDb('test')
        db.put_shortcut('google', 'g', 'http://google', 'icon', True)
        db.put_shortcut('google maps', 'maps', 'http://maps.google', 'icon', True)
        db.put_shortcut('google calendar', 'cal', 'http://cal.google', 'icon', True)
        db.put_shortcut('google music', 'm', 'http://music.google', 'icon', True)
        return db

    def test_get_sorted_records(self, db):
        records = db.get_sorted_records()
        assert records[0]['name'] == 'google'
        assert records[3]['name'] == 'google music'

    def test_put_shortcut(self, db):
        assert db.put_shortcut('google play', 'p', 'http://play.google', 'icon', True)
        assert db.put_shortcut('google play', 'p', 'http://play.google', 'icon', True, id='uuid123') == 'uuid123'
