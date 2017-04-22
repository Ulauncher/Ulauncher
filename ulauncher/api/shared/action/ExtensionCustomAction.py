import pickle
from gi.repository import GLib

from ulauncher.api.shared.event import ItemEnterEvent
from .BaseAction import BaseAction


class ExtensionCustomAction(BaseAction):

    def __init__(self, data, keep_app_open=False):
        self._data = pickle.dumps(data)
        self._keep_app_open = keep_app_open

    def keep_app_open(self):
        return self._keep_app_open

    def run(self):
        # import here to avoid circular deps
        from ulauncher.api.server.DeferredResultRenderer import DeferredResultRenderer
        from ulauncher.ui.windows.UlauncherWindow import UlauncherWindow

        window = UlauncherWindow.get_instance()
        if not window.is_visible():
            return

        renderer = DeferredResultRenderer.get_instance()
        controller = renderer.get_active_controller()
        if controller:
            controller.debounced_send_event(ItemEnterEvent(self._data))
            if not self.keep_app_open():
                GLib.idle_add(window.hide_and_clear_input)
