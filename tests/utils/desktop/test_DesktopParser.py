import os
import pytest
from ulauncher.utils.desktop.DesktopParser import DesktopParser

desktop_content = """
[Section Name]
Test=123

[Desktop Entry]
Name=Ulauncher
Comment=Ulauncher comment
Categories=GNOME;Utility;
Exec=/usr/bin/ul
Icon=app.svg
Terminal=false
Type=Application

[Another Section]
Hello=World
"""


class TestDesktopParser:

    @pytest.fixture
    def desktop_file(self, tmpdir):
        """
        Returns path to a desktop file
        """
        pathname = os.path.join(str(tmpdir), 'appname.desktop')
        with open(pathname, 'w') as f:
            f.write(desktop_content)
        return pathname

    @pytest.fixture
    def parser(self, desktop_file):
        return DesktopParser(desktop_file)

    def get_lines(self, desktop_file):
        with open(desktop_file, 'r') as f:
            return [line.strip(' %s' % os.linesep) for line in f.readlines()]

    def test_get(self, parser):
        assert parser.get('Name') == 'Ulauncher'
        with pytest.raises(KeyError):
            parser.get('Hello')
        with pytest.raises(KeyError):
            parser.get('Test')

    def test_set(self, parser):
        parser.set('Name', 'New Name')
        assert parser.get('Name') == 'New Name'
        parser.set('test_set', 'true')
        assert parser.get('test_set') == 'true'

    def test_write(self, parser, tmpdir):
        filename = os.path.join(str(tmpdir), 'newappname.desktop')
        parser.set('Name', 'New Name')
        parser.set_filename(filename)
        parser.write()

        lines = self.get_lines(filename)
        assert '[Desktop Entry]' in lines
        assert 'Name=New Name' in lines

    def test_write__to_nonexistent_dir(self, tmpdir, parser):
        filename = os.path.join(str(tmpdir), 'subdir', 'subdir2', 'newappname3.desktop')
        parser.set('Name', 'New Name 3')
        parser.set_filename(filename)
        parser.write()

        lines = self.get_lines(filename)
        assert '[Desktop Entry]' in lines
        assert 'Name=New Name 3' in lines

    def test_get_boolean(self, parser):
        assert parser.get_boolean('Terminal') is False
        parser.set('Terminal', 'on')
        assert parser.get_boolean('Terminal') is True
        parser.set('Terminal', 'trUe')
        assert parser.get_boolean('Terminal') is True
        parser.set('Terminal', '338')
        with pytest.raises(ValueError):
            parser.get_boolean('Terminal')
