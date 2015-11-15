import os
import pytest
from ulauncher.utils.Path import Path, InvalidPathError


class TestPath:

    def test_get_existing_dir(self):
        assert Path('/usr/bin').get_existing_dir() == '/usr/bin'
        assert Path('/usr/bin/foo').get_existing_dir() == '/usr/bin'
        assert Path('/usr/bin/foo/bar').get_existing_dir() == '/usr/bin'
        assert Path('/usr/bin/.').get_existing_dir() == '/usr/bin'
        assert Path('/usr/bin/sh').get_existing_dir() == '/usr/bin'
        assert Path('~/foo/bar').get_existing_dir() == os.path.expanduser('~')

    def test_get_existing_dir__caches(self, mocker):
        path = Path('/usr/bin/foo')
        assert path.get_existing_dir() == '/usr/bin'
        os_path_exitst = mocker.patch('ulauncher.utils.Path.os.path.exists')
        assert path.get_existing_dir() == '/usr/bin'
        assert path.get_existing_dir() == '/usr/bin'
        assert not os_path_exitst.called

    def test_get_existing_dir__raises(self):
        with pytest.raises(InvalidPathError):
            assert Path('~~').get_existing_dir()

    def test_get_search_part(self):
        assert Path('/usr/bin').get_search_part() == ''
        assert Path('/usr/bin/foo').get_search_part() == 'foo'
        assert Path('/usr/bin/foo/bar').get_search_part() == 'foo/bar'
        assert Path('~/foo/bar/').get_search_part() == 'foo/bar'

    def test_get_user_path(self):
        assert Path('/bin').get_user_path() == '/bin'
        assert Path('/usr/bin/foo').get_user_path() == '/usr/bin/foo'
        assert Path('~/foo/bar//').get_user_path() == '~/foo/bar'

    def test_get_basename(self):
        assert Path('/bin').get_basename() == 'bin'
        assert Path('/usr/bin/My Videos').get_basename() == 'My Videos'
        assert Path('~/foo/bar//').get_basename() == 'bar'

    def test_get_dirname(self):
        assert Path('~/Pictures/').get_dirname() == '~'
        assert Path('~/').get_dirname() == ''
        assert Path('~').get_dirname() == ''
        assert Path('/').get_dirname() == ''
        assert Path('/usr/bin/foo').get_dirname() == '/usr/bin'
