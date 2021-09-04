import os
import pytest
from ulauncher.search.shortcuts.ShortcutsDb import ShortcutsDb


class TestShortcutsDb:

    @pytest.fixture(autouse=True)
    def get_default_shortcuts(self, mocker):
        default = mocker.patch('ulauncher.search.shortcuts.ShortcutsDb.get_default_shortcuts')
        default.return_value = []
        return default

    @pytest.fixture
    def db(self, tmpdir):
        db = ShortcutsDb(os.path.join(str(tmpdir), 'shortcuts.json'))
        db.put_shortcut('google', 'g', 'https://google', 'icon', True, False)
        db.put_shortcut('google maps', 'maps', 'https://maps.google', 'icon', True, False)
        db.put_shortcut('google calendar', 'cal', 'https://cal.google', 'icon', True, False)
        db.put_shortcut('google music', 'm', 'https://music.google', 'icon', True, False)
        return db

    def test_get_sorted_records(self, db):
        records = db.get_sorted_records()
        assert records[0]['name'] == 'google'
        assert records[3]['name'] == 'google music'

    def test_put_shortcut(self, db):
        assert db.put_shortcut('googleplay', 'p', 'https://play.google', 'icon', True, False)
        assert db.put_shortcut('googleplay', 'p', 'https://play.google', 'icon', True, False, id='uuid123') == 'uuid123'

    def test_commit__ensures_user_path(self, db, mocker):
        expanduser = mocker.patch('ulauncher.search.shortcuts.ShortcutsDb.os.path.expanduser')
        expanduser.return_value = '/home/username'
        db.put_shortcut('test shortcut', 't', 'https://example.com',
                        '/home/username/dir/~/file', True, False, id='test1')
        db.commit()
        assert db.find('test1')['icon'] == '~/dir/~/file'
