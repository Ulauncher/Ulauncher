import pytest
import mock
from ulauncher.PreferencesUlauncherDialog import PreferencesUlauncherDialog
from gi.repository import Gtk


class TestPreferencesUlauncherDialog:

    @pytest.fixture(autouse=True)
    def settings(self, mocker):
        return mocker.patch('ulauncher.PreferencesUlauncherDialog.getSettings').return_value

    @pytest.fixture(autouse=True)
    def indicator(self, mocker):
        return mocker.patch('ulauncher.PreferencesUlauncherDialog.getIndicator').return_value

    @pytest.fixture(autouse=True)
    def ulauncherWindow(self, mocker):
        return mocker.patch('ulauncher.PreferencesUlauncherDialog.getUlauncherWindow').return_value

    @pytest.fixture
    def builder(self):
        """
        builder.get_object() returns the one mock object for one name
        """
        builder = mock.MagicMock()
        objects = {}

        def get_object(name):
            try:
                return objects[name]
            except KeyError:
                o = mock.MagicMock(name=name)
                objects[name] = o
                return o

        builder.get_object.side_effect = get_object
        return builder

    @pytest.fixture
    def dialog(self, builder):
        dialog = PreferencesUlauncherDialog()
        dialog.finish_initializing(builder)
        return dialog

    def test_finish_initializing(self, dialog, builder, settings):
        # it removes dialog_action_area
        builder.get_object('dialog_action_area').destroy.assert_called_with()

        builder.get_object('show_indicator_icon').set_active.assert_called_with(settings.get_property.return_value)
        builder.get_object('hotkey_show_app').set_text.assert_called_with('Ctrl+Space')

    def test_on_show_indicator_icon_notify(self, dialog, builder, settings, indicator):
        widget = mock.MagicMock()
        event = mock.MagicMock()
        event.name = 'active'

        widget.get_active.return_value = True
        dialog.on_show_indicator_icon_notify(widget, event)
        indicator.show.assert_called_with()
        settings.set_property.assert_called_with('show-indicator-icon', True)

        widget.get_active.return_value = False
        dialog.on_show_indicator_icon_notify(widget, event)
        indicator.hide.assert_called_with()
        settings.set_property.assert_called_with('show-indicator-icon', False)
        settings.save_to_file.assert_called_with()

    def test_on_hotkey_show_app_key_press_event__invalid_hotkey(self, dialog, ulauncherWindow):
        widget = mock.MagicMock()
        event = mock.MagicMock()
        (key, mode) = Gtk.accelerator_parse('BackSpace')
        event.keyval = key
        event.state = mode

        dialog.on_hotkey_show_app_key_press_event(widget, event)

        assert not ulauncherWindow.bind_show_app_hotkey.called
        assert not widget.set_text.called

    def test_on_hotkey_show_app_key_press_event__valid_hotkey(self, dialog, ulauncherWindow, settings):
        widget = mock.MagicMock()
        event = mock.MagicMock()
        accel_name = '<Primary><Alt>g'
        (key, mode) = Gtk.accelerator_parse(accel_name)
        event.keyval = key
        event.state = mode

        dialog.on_hotkey_show_app_key_press_event(widget, event)

        ulauncherWindow.bind_show_app_hotkey.assert_called_with(accel_name)
        widget.set_text.assert_called_with('Ctrl+Alt+G')
        settings.set_property.assert_called_with('hotkey-show-app', accel_name)
        settings.save_to_file.assert_called_with()
