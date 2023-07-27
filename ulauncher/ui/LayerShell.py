import logging

import gi
from gi.repository import Gtk

logger = logging.getLogger()

try:
    gi.require_version("GtkLayerShell", "0.1")
    from gi.repository import GtkLayerShell  # type: ignore[attr-defined]
except (ValueError, ImportError):
    GtkLayerShell = None


class LayerShellOverlay(Gtk.Window):
    """
    Allows for a window to opt in to the wayland layer shell protocol.

    This Disables decorations and displays the window on top of other applications (even if fullscreen).
    Uses the wlr-layer-shell protocol [1]

    [1]: https://gitlab.freedesktop.org/wlroots/wlr-protocols/-/blob/master/unstable/wlr-layer-shell-unstable-v1.xml
    """

    @classmethod
    def is_supported(cls):
        """Check if running under a wayland compositor that supports the layer shell extension"""
        return GtkLayerShell is not None and GtkLayerShell.is_supported()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._use_layer_shell = False

    def enable_layer_shell(self):
        assert __class__.is_supported(), "Should be supported to enable"
        self._use_layer_shell = True

        GtkLayerShell.init_for_window(self)
        GtkLayerShell.set_keyboard_mode(self, GtkLayerShell.KeyboardMode.EXCLUSIVE)
        GtkLayerShell.set_layer(self, GtkLayerShell.Layer.OVERLAY)
        # Ask to be moved when over some other shell component
        GtkLayerShell.set_exclusive_zone(self, 0)

    @property
    def layer_shell_enabled(self):
        return self._use_layer_shell

    def set_vertical_position(self, pos_y):
        # Set vertical position and anchor to the top edge, will be centered horizontally
        # by default
        GtkLayerShell.set_anchor(self, GtkLayerShell.Edge.TOP, True)
        GtkLayerShell.set_margin(self, GtkLayerShell.Edge.TOP, pos_y)
