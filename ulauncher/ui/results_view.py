from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Callable

from gi.repository import Gdk, Gtk

from ulauncher.utils import scheduling

if TYPE_CHECKING:
    from ulauncher.internals.result import Result
    from ulauncher.internals.results_update import ResultsUpdate
    from ulauncher.ui.result_widget import ResultWidget
    from ulauncher.utils.settings import Settings

logger = logging.getLogger(__name__)


class ResultsView(Gtk.ScrolledWindow):
    """Scrollable list of results, owning the result widgets and the selection within them."""

    _has_wrapped_results = False
    _index = 0

    def __init__(self, settings: Settings, apply_css: Callable[[Gtk.Widget], None]) -> None:
        super().__init__(
            can_focus=True,
            hscrollbar_policy=Gtk.PolicyType.NEVER,
            propagate_natural_height=True,
            shadow_type=Gtk.ShadowType.IN,
        )
        self._settings = settings
        self._apply_css = apply_css
        self._widgets: list[ResultWidget] = []
        self._box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self._box.get_style_context().add_class("result-box")
        self._box.connect("size-allocate", self._fit_results_height)
        self.add(self._box)

    @property
    def has_results(self) -> bool:
        return bool(self._widgets)

    def set_max_height(self, height: int) -> None:
        self.set_property("max-content-height", height)

    def render(self, update: ResultsUpdate) -> None:
        from ulauncher.ui.result_widget import ResultWidget

        self._box.foreach(lambda w: w.destroy())
        self._widgets = []
        self._index = 0

        jump_keys = self._settings.get_jump_keys()
        limit = len(jump_keys) or 25
        result_list = update["results"][:limit]
        # stock sizing works for single-line results; only wrapped ones need _fit_results_height
        self._has_wrapped_results = any(result.wrap for result in result_list)
        if not self._has_wrapped_results:
            self.set_min_content_height(-1)  # restore stock sizing

        if not result_list:
            # Hide the scroll container when there are no results since it normally takes up a
            # minimum amount of space even if it is empty.
            self.hide()
            logger.debug("Hiding results container, no results found")
            return

        for index, result in enumerate(result_list):
            widget = ResultWidget(result, index, update["query"], jump_keys)
            self._widgets.append(widget)
            self._box.add(widget)

        self.select(self._index_for_name(update["selected_name"]))
        self._box.set_margin_bottom(10)
        self._box.set_margin_top(3)
        self._apply_css(self._box)
        self.show_all()
        logger.debug("Render %s results", len(self._widgets))

    def go_up(self) -> None:
        self.select((self._index or len(self._widgets)) - 1)

    def go_down(self) -> None:
        next_index = self._index + 1
        self.select(next_index if next_index < len(self._widgets) else 0)

    def get_active_result(self) -> Result | None:
        selected = self._selected
        return selected.result if selected else None

    def select(self, index: int) -> None:
        if not self._widgets:
            return
        if not 0 <= index < len(self._widgets):
            index = 0
        if self._selected:
            self._selected.deselect()
        self._index = index
        self._widgets[index].select()

    @property
    def _selected(self) -> ResultWidget | None:
        if len(self._widgets) > self._index:
            return self._widgets[self._index]
        return None

    def _index_for_name(self, name: str | None) -> int:
        """Index of the first searchable result with this name, or 0 if none matches."""
        for index, widget in enumerate(self._widgets):
            if widget.result.searchable and widget.result.name == name:
                return index
        return 0

    def _fit_results_height(self, box: Gtk.Box, allocation: Gdk.Rectangle) -> None:
        """GtkScrolledWindow measures its natural height without height-for-width,
        clipping wrapped (Result.wrap) labels - request the real height instead."""
        if not self._has_wrapped_results or allocation.width <= 0:
            return  # nothing to fit, or an early allocation pass with no usable width yet
        current_height = self.get_min_content_height()
        max_height = self.get_property("max-content-height")
        needed_height = box.get_preferred_height_for_width(allocation.width)[1]
        if max_height > 0:
            needed_height = min(needed_height, max_height)
        if abs(needed_height - current_height) > 1:  # tolerance: a scrollbar can shift the width by ~1px
            self.set_min_content_height(needed_height)
            # the in-progress allocation pass ignores the new request
            scheduling.run_when_idle(self.queue_resize)
