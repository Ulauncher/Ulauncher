import os
import pytest
from ulauncher.utils.AutostartPreference import AutostartPreference, SwitchError
import ulauncher.utils.AutostartPreference as ap


desktop_content = """
[Desktop Entry]
Name=Ulauncher
Comment=Provides a convenient and fast way to launch your desktop applications
Categories=GNOME;Utility;
Exec=/usr/bin/ulauncher
Icon=/usr/share/ulauncher/media/ulauncher.svg
Terminal=false
Type=Application
"""


class TestAutostartPreference:

    @pytest.fixture(autouse=True)
    def desktop_file(self, tmpdir):
        """
        Returns path to a desktop file
        """
        pathname = os.path.join(str(tmpdir), 'ulauncher-orig.desktop')
        with open(pathname, 'w') as f:
            f.write(desktop_content)
        return pathname

    @pytest.fixture(autouse=True)
    def xdg_config_home(self, tmpdir):
        ap.xdg_config_home = os.path.join(str(tmpdir), 'xdg_config_home')
        return ap.xdg_config_home

    @pytest.fixture
    def autostart_path(self, xdg_config_home):
        path = os.path.join(xdg_config_home, 'autostart')
        if not os.path.exists(path):
            os.makedirs(path)
        return path

    @pytest.fixture(autouse=True)
    def db(self, mocker, desktop_file):
        db = mocker.patch('ulauncher.utils.AutostartPreference.AppDb.get_instance').return_value
        db.get_by_name.return_value = {'name': 'Ulauncher', 'desktop_file': desktop_file}
        return db

    @pytest.fixture
    def autostart(self):
        return AutostartPreference()

    def get_lines(self, desktop_file):
        with open(desktop_file, 'r') as f:
            return [line.strip(' %s' % os.linesep) for line in f.readlines()]

    def test_is_allowed__returns_True(self, autostart):
        assert autostart.is_allowed()

    def test_is_allowed__returns_False(self, db):
        db.get_by_name.return_value = None
        assert not AutostartPreference().is_allowed()

    def test_is_on__returns_True(self, autostart, autostart_path):
        with open(os.path.join(autostart_path, 'ulauncher.desktop'), 'w') as f:
            f.write(''.join((desktop_content, 'X-GNOME-Autostart-enabled=true\n')))
        assert autostart.is_on()

    def test_is_on__returns_False(self, autostart, autostart_path):
        assert not autostart.is_on()

        with open(os.path.join(autostart_path, 'ulauncher.desktop'), 'w') as f:
            f.write(desktop_content)
        assert not autostart.is_on()

    def test_switch__raises_when_not_allowed(self, autostart, mocker):
        is_allowed = mocker.patch.object(autostart, 'is_allowed')
        is_allowed.return_value = False
        with pytest.raises(SwitchError):
            autostart.switch(True)

    def test_switch__on_when_autostart_exists(self, autostart, autostart_path):
        ul_autostart_path = os.path.join(autostart_path, 'ulauncher.desktop')
        with open(ul_autostart_path, 'w') as f:
            f.write(''.join((desktop_content, 'X-GNOME-Autostart-enabled=false\n')))
        autostart.switch(True)
        assert 'X-GNOME-Autostart-enabled=true' in self.get_lines(ul_autostart_path)
        assert 'Exec=/usr/bin/ulauncher --hide-window' in self.get_lines(ul_autostart_path)

    def test_switch__on_when_autostart_doesnt_exist(self, autostart, autostart_path):
        ul_autostart_path = os.path.join(autostart_path, 'ulauncher.desktop')
        autostart.switch(True)
        assert 'X-GNOME-Autostart-enabled=true' in self.get_lines(ul_autostart_path)

    def test_switch__off_when_autostart_doesnt_exist(self, autostart, autostart_path):
        ul_autostart_path = os.path.join(autostart_path, 'ulauncher.desktop')
        autostart.switch(False)
        assert 'X-GNOME-Autostart-enabled=false' in self.get_lines(ul_autostart_path)

    def test_switch__raises_SwitchError(self, autostart, mocker):
        desktop_parser = mocker.patch('ulauncher.utils.AutostartPreference.DesktopParser').return_value
        desktop_parser.write.side_effect = IOError
        with pytest.raises(SwitchError):
            autostart.switch(True)
