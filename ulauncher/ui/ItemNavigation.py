from __future__ import annotations

from ulauncher.api.shared.query import Query
from ulauncher.config import PATHS
from ulauncher.ui.ResultWidget import ResultWidget
from ulauncher.utils.eventbus import EventBus
from ulauncher.utils.json_utils import json_load, json_save

events = EventBus()
query_history_path = f"{PATHS.STATE}/query_history.json"
query_history: dict[str, str] = json_load(query_history_path)


class ItemNavigation:
    """
    Performs navigation through found results
    """

    result_widgets: list[ResultWidget]

    index = 0

    def __init__(self, result_widgets: list[ResultWidget]) -> None:
        self.result_widgets = result_widgets

    @property
    def selected_item(self) -> ResultWidget | None:
        if len(self.result_widgets) > self.index:
            return self.result_widgets[self.index]
        return None

    def get_default(self, query: Query) -> int:
        """
        Get the index of the result that should be selected (0 by default)
        """
        previous_pick = query_history.get(query)

        for index, widget in enumerate(self.result_widgets):
            if widget.result.searchable and widget.result.name == previous_pick:
                return index
        return 0

    def select_default(self, query: Query) -> None:
        self.select(self.get_default(query))

    def select(self, index: int) -> None:
        if not 0 < index < len(self.result_widgets):
            index = 0

        if self.selected_item:
            self.selected_item.deselect()

        self.index = index
        self.result_widgets[index].select()

    def go_up(self) -> None:
        self.select((self.index or len(self.result_widgets)) - 1)

    def go_down(self) -> None:
        next_result = (self.index or 0) + 1
        self.select(next_result if next_result < len(self.result_widgets) else 0)

    def activate(self, query: Query, alt: bool = False) -> None:
        assert self.selected_item
        result = self.selected_item.result
        if query and not alt and result.searchable:
            query_history[str(query)] = result.name
            json_save(query_history, query_history_path)

        events.emit("mode:handle_action", result.on_activation(query, alt))
