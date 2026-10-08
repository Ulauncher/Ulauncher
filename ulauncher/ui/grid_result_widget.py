from __future__ import annotations

from typing import TYPE_CHECKING, Callable

from gi.repository import Gtk, Pango

from ulauncher.ui.load_icon_surface import load_icon_surface
from ulauncher.ui.result_widget import ResultWidgetBase

if TYPE_CHECKING:
    from ulauncher.internals.query import Query
    from ulauncher.internals.result import Result
    from ulauncher.utils.settings import RecentAppsGridLabels

MIN_ICON_SIZE = 16
MAX_ICON_SIZE = 128
# Two lines of a ~14 character name is enough for most app names without widening the tile
NAME_MAX_CHARS = 14
NAME_MAX_LINES = 2


def _styled(widget: Gtk.Widget, *class_names: str) -> None:
    style_context = widget.get_style_context()
    for class_name in class_names:
        style_context.add_class(class_name)


class GridResultWidget(ResultWidgetBase):
    """A result rendered as a tile: icon on top, optional name and jump key underneath.

    Used by the frequent apps grid. Deliberately skips query highlighting and descriptions, since
    the grid only ever shows on an empty query.
    """

    name_label: Gtk.Label | None = None

    def __init__(
        self,
        result: Result,
        index: int,
        query: Query,
        on_select: Callable[[int], None],
        on_activate: Callable[[int, bool], None],
        jump_keys: list[str],
        icon_size: int = 48,
        labels: RecentAppsGridLabels = "name-and-shortcut",
    ) -> None:
        self._init_base(result, query, on_select, on_activate, jump_keys)
        icon_size = min(MAX_ICON_SIZE, max(MIN_ICON_SIZE, icon_size))

        super().__init__()
        self.get_style_context().add_class("item-frame")
        self.get_style_context().add_class("grid-item-frame")
        self.connect("button-release-event", self.on_click)
        self.connect("enter_notify_event", self.on_mouse_hover)

        self.item_box = Gtk.EventBox()
        _styled(self.item_box, "item-box", "grid-item-box")
        self.add(self.item_box)

        container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, halign=Gtk.Align.CENTER)
        _styled(container, "item-container", "grid-item-container")
        self.item_box.add(container)

        icon = Gtk.Image(halign=Gtk.Align.CENTER)
        icon.set_from_surface(load_icon_surface(result.icon or "gtk-missing-image", icon_size, self.get_scale_factor()))
        icon.set_size_request(icon_size, icon_size)
        _styled(icon, "item-icon", "grid-item-icon")
        container.pack_start(icon, False, True, 0)

        if labels in ("name", "name-and-shortcut"):
            self.name_label = Gtk.Label(
                label=result.name,
                halign=Gtk.Align.CENTER,
                justify=Gtk.Justification.CENTER,
                wrap=True,
                wrap_mode=Pango.WrapMode.WORD_CHAR,
                lines=NAME_MAX_LINES,
                ellipsize=Pango.EllipsizeMode.END,
                max_width_chars=NAME_MAX_CHARS,
                xalign=0.5,
            )
            _styled(self.name_label, "item-name", "item-text", "grid-item-name")
            container.pack_start(self.name_label, False, True, 0)

        if labels in ("shortcut", "name-and-shortcut"):
            self.shortcut_label = Gtk.Label(halign=Gtk.Align.CENTER, justify=Gtk.Justification.CENTER, xalign=0.5)
            _styled(self.shortcut_label, "item-shortcut", "item-text", "grid-item-shortcut")
            container.pack_start(self.shortcut_label, False, True, 0)

        self.set_index(index)
