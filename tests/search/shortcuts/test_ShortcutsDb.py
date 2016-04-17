import os
import pytest
import mock
from ulauncher.search.shortcuts.ShortcutsDb import ShortcutsDb


class TestShortcutsDb(object):

    @pytest.fixture
    def db(self):
        db = ShortcutsDb('test')
        db.put_shortcut('google', 'g', 'http://google', 'icon')
        db.put_shortcut('google maps', 'maps', 'http://maps.google', 'icon')
        db.put_shortcut('google calendar', 'cal', 'http://cal.google', 'icon')
        db.put_shortcut('google music', 'm', 'http://music.google', 'icon')
        return db

    def test_get_sorted_records(self, db):
        records = db.get_sorted_records()
        assert records[0]['name'] == 'google'
        assert records[3]['name'] == 'google music'

    def test_put_shortcut(self, db):
        assert db.put_shortcut('google play', 'p', 'http://play.google', 'icon')
        assert db.put_shortcut('google play', 'p', 'http://play.google', 'icon', id='uuid123') == 'uuid123'
