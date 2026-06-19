from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ulauncher.internals.result import Result
    from ulauncher.ui.result_widget import ResultWidget


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

    def _get_index_by_name(self, name: str | None) -> int:
        """Index of the first searchable result with this name, or 0 if none matches."""
        for index, widget in enumerate(self.result_widgets):
            if widget.result.searchable and widget.result.name == name:
                return index
        return 0

    def select_by_name(self, name: str | None) -> None:
        self.select(self._get_index_by_name(name))

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

    def get_active_result(self) -> Result | None:
        if self.selected_item:
            return self.selected_item.result
        return None
