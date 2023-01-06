from unittest import mock
import pytest
from gi.repository import Gtk
from ulauncher.ui.windows.HotkeyDialog import HotkeyDialog


class TestHotkeyDialog:
    @pytest.fixture
    def dialog(self):
        dialog = HotkeyDialog()
        dialog._hotkey_input = mock.MagicMock()
        return dialog

    @pytest.fixture
    def event(self):
        return mock.MagicMock()

    @pytest.fixture
    def widget(self):
        return mock.MagicMock()

    @pytest.fixture
    def emit(self, dialog, mocker):
        mocker.patch.object(dialog, "emit")
        return dialog.emit

    def test_on_key_press__invalid_hotkey(self, dialog, widget, event):
        (key, mode) = Gtk.accelerator_parse("BackSpace")
        event.keyval = key
        event.state = mode

        dialog.on_key_press(widget, event)
        assert not dialog._hotkey_input.set_text.called

    def test_on_key_press__valid_hotkey(self, dialog, widget, event, emit):
        accel_name = "<Primary><Alt>g"
        (key, mode) = Gtk.accelerator_parse(accel_name)
        event.keyval = key
        event.state = mode

        dialog.on_key_press(widget, event)
        dialog._hotkey_input.set_text.assert_called_with("Ctrl+Alt+G")

        # hit Return
        return_accel_name = "Return"
        (key, mode) = Gtk.accelerator_parse(return_accel_name)
        event.keyval = key
        event.state = mode
        dialog.on_key_press(widget, event)

        emit.assert_called_with("hotkey-set", accel_name, "Ctrl+Alt+G")
