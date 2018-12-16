import pytest
import mock
from gi.repository import Gtk
from ulauncher.ui.windows.HotkeyDialog import HotkeyDialog


class TestHotkeyDialog:

    @pytest.fixture
    def dialog(self, mocker):
        mocker.patch('ulauncher.ui.windows.HotkeyDialog.HotkeyDialog.finish_initializing')
        dialog = HotkeyDialog()
        dialog.ui = mock.MagicMock()
        dialog.builder = mock.MagicMock()
        return dialog

    @pytest.fixture
    def event(self):
        return mock.MagicMock()

    @pytest.fixture
    def widget(self):
        return mock.MagicMock()

    @pytest.fixture
    def emit(self, dialog, mocker):
        mocker.patch.object(dialog, 'emit')
        return dialog.emit

    def test_on_hotkey_input_key_press_event__invalid_hotkey(self, dialog, widget, event):
        (key, mode) = Gtk.accelerator_parse('BackSpace')
        event.keyval = key
        event.state = mode

        dialog.on_hotkey_input_key_press_event(widget, event)
        assert not dialog.ui['hotkey_input'].set_text.called

    @pytest.mark.with_display
    def test_on_hotkey_input_key_press_event__valid_hotkey(self, dialog, widget, event, emit):
        accel_name = '<Primary><Alt>g'
        (key, mode) = Gtk.accelerator_parse(accel_name)
        event.keyval = key
        event.state = mode

        dialog.on_hotkey_input_key_press_event(widget, event)
        dialog.ui['hotkey_input'].set_text.assert_called_with('Ctrl+Alt+G')

        # hit Return
        return_accel_name = 'Return'
        (key, mode) = Gtk.accelerator_parse(return_accel_name)
        event.keyval = key
        event.state = mode
        dialog.on_hotkey_input_key_press_event(widget, event)

        emit.assert_called_with('hotkey-set', accel_name, 'Ctrl+Alt+G')
