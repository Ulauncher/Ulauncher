from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Callable

from gi.repository import Gdk, Gtk

from ulauncher.utils import scheduling

if TYPE_CHECKING:
    from ulauncher.internals.query import Query
    from ulauncher.internals.result import Result
    from ulauncher.internals.results_update import ResultsUpdate
    from ulauncher.ui.result_widget import ResultWidget
    from ulauncher.utils.settings import Settings

logger = logging.getLogger(__name__)


class ResultsView(Gtk.ScrolledWindow):
    """Scrollable list of results, owning the result widgets and the selection within them."""

    _has_wrapped_results = False
    _index = 0
    _user_selected = False  # True once the user actively moved the selection (keyboard/mouse)
    _query = ""

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
        # A new query resets navigation; streamed batches of the same query keep the user's pick.
        if str(update["query"]) != self._query:
            self._query = str(update["query"])
            self._user_selected = False

        if update["append"] and self._widgets:
            self._append_results(update)
        else:
            self._replace_results(update)

    def get_active_result(self) -> Result | None:
        selected = self._selected
        return selected.result if selected else None

    def select(self, index: int) -> None:
        self._select(index)
        self._user_selected = True

    def go_up(self) -> None:
        self.select((self._index or len(self._widgets)) - 1)

    def go_down(self) -> None:
        next_index = self._index + 1
        self.select(next_index if next_index < len(self._widgets) else 0)

    def _replace_results(self, update: ResultsUpdate) -> None:
        previous_pick = self.get_active_result() if self._user_selected else None
        self._box.foreach(lambda w: w.destroy())
        self._widgets = []
        self._index = 0

        result_list = update["results"][: self._limit()]
        # stock sizing works for single-line results; only wrapped ones need _fit_results_height
        self._has_wrapped_results = any(result.wrap for result in result_list)
        if not self._has_wrapped_results:
            self.set_min_content_height(-1)  # restore stock sizing

        if not result_list:
            # Hide the scroll container when there are no results since it normally takes up a
            # minimum amount of space even if it is empty.
            self._user_selected = False
            self.hide()
            logger.debug("Hiding results container, no results found")
            return

        self._add_widgets(result_list, update["query"], start_index=0)
        self._apply_selection(update["selected_name"], previous_pick)
        self._box.set_margin_bottom(10)
        self._box.set_margin_top(3)
        self._apply_css(self._box)
        self.show_all()
        logger.debug("Render %s results", len(self._widgets))

    def _append_results(self, update: ResultsUpdate) -> None:
        existing = len(self._widgets)
        new_results = update["results"][: max(0, self._limit() - existing)]
        if not new_results:
            return
        if any(result.wrap for result in new_results):
            self._has_wrapped_results = True
        self._add_widgets(new_results, update["query"], start_index=existing)
        # keep the user's pick; only (re)evaluate the default when they haven't navigated
        if not self._user_selected:
            self._apply_selection(update["selected_name"], None)
        self._apply_css(self._box)
        self.show_all()
        logger.debug("Append %s results (%s total)", len(new_results), len(self._widgets))

    def _add_widgets(self, results: list[Result], query: Query, start_index: int) -> None:
        from ulauncher.ui.result_widget import ResultWidget

        jump_keys = self._settings.get_jump_keys()
        for offset, result in enumerate(results):
            widget = ResultWidget(result, start_index + offset, query, jump_keys)
            self._widgets.append(widget)
            self._box.add(widget)

    def _apply_selection(self, selected_name: str | None, previous_pick: Result | None) -> None:
        # Keep the user's pick across a streaming replace if it is still present.
        if previous_pick:
            for index, widget in enumerate(self._widgets):
                if widget.result.name == previous_pick.name:
                    self.select(index)
                    return
            self._user_selected = False
        self._select(self._index_for_name(selected_name))

    def _select(self, index: int) -> None:
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

    def _limit(self) -> int:
        return len(self._settings.get_jump_keys()) or 25

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
