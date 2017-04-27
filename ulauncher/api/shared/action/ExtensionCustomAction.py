import pickle

from ulauncher.api.shared.event import ItemEnterEvent
from .BaseAction import BaseAction


class ExtensionCustomAction(BaseAction):
    """
    If initiated with ``data``, the same data will be returned
    in :class:`~ulauncher.api.shared.event.ItemEnterEvent` object

    :param any data: any type that can be serialized with :func:`pickle.dumps`
    :param bool keep_app_open: pass ``True`` if you want to keep Ulauncher window open.
                               ``False`` by default
    """

    def __init__(self, data, keep_app_open=False):
        self._data = pickle.dumps(data)
        self._keep_app_open = keep_app_open

    def keep_app_open(self):
        return self._keep_app_open

    def run(self):
        """
        Runs :meth:`~ulauncher.api.server.ExtensionController.ExtensionController.trigger_event`
        with :class:`ItemEnterEvent`
        """
        # import here to avoid circular deps
        from ulauncher.api.server.DeferredResultRenderer import DeferredResultRenderer
        from ulauncher.ui.windows.UlauncherWindow import UlauncherWindow

        window = UlauncherWindow.get_instance()
        if not window.is_visible():
            return

        renderer = DeferredResultRenderer.get_instance()
        controller = renderer.get_active_controller()
        if controller:
            controller.trigger_event(ItemEnterEvent(self._data))
