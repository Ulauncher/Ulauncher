from __future__ import annotations

from types import SimpleNamespace
from typing import Any, cast
from unittest.mock import MagicMock

import pytest
from gi.repository import Gtk
from pytest_mock import MockerFixture

from ulauncher.internals.query import Query
from ulauncher.internals.result import Result
from ulauncher.internals.results_update import ResultsUpdate, results_update
from ulauncher.ui.results_view import TILE_EXTRA_WIDTH, ResultsView
from ulauncher.ui.ulauncher_window import UlauncherWindow


def _named_widget(name: str, *, searchable: bool = True) -> MagicMock:
    widget = MagicMock()
    widget.result.name = name
    widget.result.searchable = searchable
    return widget


class TestResultsView:
    @pytest.mark.parametrize(
        ("has_wrapped", "width", "current_min", "needed", "measured_width", "expected_min", "expects_resize"),
        [
            pytest.param(True, 500, 46, 180, 500, 180, True, id="requests_the_height_for_width"),
            pytest.param(True, 500, 46, 2000, 500, 600, True, id="clamps_to_max_content_height"),
            pytest.param(True, 500, 180, 180, 500, None, False, id="noop_when_height_is_unchanged"),
            pytest.param(True, 500, 180, 181, 500, None, False, id="tolerates_one_pixel_oscillation"),
            pytest.param(True, 0, 46, 180, None, None, False, id="skips_early_allocation_passes"),
            pytest.param(False, 500, 180, 180, None, None, False, id="noop_without_wrapped_results"),
        ],
    )
    def test_fit_results_height(
        self,
        mocker: MockerFixture,
        has_wrapped: bool,
        width: int,
        current_min: int,
        needed: int,
        measured_width: int | None,
        expected_min: int | None,
        expects_resize: bool,
    ) -> None:
        run_when_idle = mocker.patch("ulauncher.ui.results_view.scheduling.run_when_idle")
        box = MagicMock()
        box.get_preferred_height_for_width.return_value = (needed, needed)
        # a fake self lets us drive the scroller's reported heights directly
        view = cast(
            "Any",
            SimpleNamespace(
                _has_wrapped_results=has_wrapped,
                get_min_content_height=MagicMock(return_value=current_min),
                get_property=MagicMock(return_value=600),  # max-content-height
                set_min_content_height=MagicMock(),
                queue_resize=MagicMock(),
            ),
        )

        ResultsView._fit_results_height(view, box, cast("Any", SimpleNamespace(width=width)))

        if measured_width is None:
            box.get_preferred_height_for_width.assert_not_called()
        else:
            box.get_preferred_height_for_width.assert_called_once_with(measured_width)

        if expected_min is None:
            view.set_min_content_height.assert_not_called()
        else:
            view.set_min_content_height.assert_called_once_with(expected_min)

        assert run_when_idle.called is expects_resize


class TestResultsViewNavigation:
    @pytest.fixture
    def items(self) -> list[MagicMock]:
        return [MagicMock() for _ in range(5)]

    @pytest.fixture
    def view(self, items: list[MagicMock]) -> ResultsView:
        view = ResultsView(cast("Any", MagicMock()), cast("Any", MagicMock()), cast("Any", MagicMock()))
        view._widgets = cast("Any", items)
        return view

    def test_select_is_called(self, view: ResultsView, items: list[MagicMock]) -> None:
        view.select(1)
        assert view._index == 1
        items[1].select.assert_called_once_with()

    def test_out_of_bounds_select_falls_back_to_first(self, view: ResultsView, items: list[MagicMock]) -> None:
        view.select(1)
        view.select(5)
        items[1].deselect.assert_called_once_with()
        items[0].select.assert_called_once_with()
        assert view._index == 0

    def test_go_up_from_start_wraps_to_last(self, view: ResultsView, items: list[MagicMock]) -> None:
        view.go_up()
        items[4].select.assert_called_once_with()

    def test_go_up(self, view: ResultsView, items: list[MagicMock]) -> None:
        view.select(1)
        view.go_up()
        items[0].select.assert_called_once_with()

    def test_go_down(self, view: ResultsView, items: list[MagicMock]) -> None:
        view.select(2)
        view.go_down()
        items[3].select.assert_called_once_with()

    def test_go_down_from_last_wraps_to_first(self, view: ResultsView, items: list[MagicMock]) -> None:
        view.select(4)
        view.go_down()
        items[0].select.assert_called_once_with()

    def test_navigation_on_empty_is_noop(self) -> None:
        view = ResultsView(cast("Any", MagicMock()), cast("Any", MagicMock()), cast("Any", MagicMock()))
        view.select(2)
        view.go_up()
        view.go_down()
        assert view.get_active_result() is None
        assert not view.has_results


class TestResultsViewGridNavigation:
    """6 tiles in 4 columns, i.e. 0 1 2 3 / 4 5"""

    @pytest.fixture
    def items(self) -> list[MagicMock]:
        return [MagicMock() for _ in range(6)]

    @pytest.fixture
    def view(self, items: list[MagicMock]) -> ResultsView:
        view = ResultsView(cast("Any", MagicMock()), cast("Any", MagicMock()), cast("Any", MagicMock()))
        view._widgets = cast("Any", items)
        view._columns = 4
        return view

    def test_columns_defaults_to_one(self) -> None:
        view = ResultsView(cast("Any", MagicMock()), cast("Any", MagicMock()), cast("Any", MagicMock()))
        assert view.columns == 1

    def test_go_right(self, view: ResultsView) -> None:
        view.go_right()
        assert view._index == 1

    def test_go_right_from_last_wraps_to_first(self, view: ResultsView) -> None:
        view.select(5)
        view.go_right()
        assert view._index == 0

    def test_go_left_from_first_wraps_to_last(self, view: ResultsView) -> None:
        view.go_left()
        assert view._index == 5

    def test_go_down_jumps_a_row(self, view: ResultsView) -> None:
        view.select(1)
        view.go_down()
        assert view._index == 5

    def test_go_down_wraps_within_the_column(self, view: ResultsView) -> None:
        view.select(5)
        view.go_down()
        assert view._index == 1

    def test_go_down_stays_put_when_the_column_has_a_single_row(self, view: ResultsView) -> None:
        view.select(3)
        view.go_down()
        assert view._index == 3

    def test_go_up_jumps_a_row(self, view: ResultsView) -> None:
        view.select(4)
        view.go_up()
        assert view._index == 0

    def test_go_up_wraps_to_the_last_populated_row_of_the_column(self, view: ResultsView) -> None:
        view.select(1)
        view.go_up()
        assert view._index == 5

    def test_navigation_on_empty_is_noop(self) -> None:
        view = ResultsView(cast("Any", MagicMock()), cast("Any", MagicMock()), cast("Any", MagicMock()))
        view._columns = 4
        view.go_up()
        view.go_down()
        view.go_left()
        view.go_right()
        assert view.get_active_result() is None


class TestGridKeyboardTakeover:
    """Horizontal arrows only belong to the grid while the input is empty."""

    @staticmethod
    def _window(columns: int) -> Any:
        # a fake self is enough: the handler only reads results_view and calls back into it
        view = MagicMock()
        view.columns = columns
        return cast("Any", SimpleNamespace(results_view=view))

    @pytest.mark.parametrize("keyname", ["Left", "Right", "Tab", "ISO_Left_Tab"])
    def test_grid_takes_the_key_while_the_input_is_empty(self, keyname: str) -> None:
        window = self._window(4)
        assert UlauncherWindow._handle_grid_navigation(window, keyname, "", has_modifier=False) is True

    @pytest.mark.parametrize("keyname", ["Left", "Right", "Tab", "ISO_Left_Tab"])
    def test_typed_text_keeps_the_key(self, keyname: str) -> None:
        """An extension can leave the grid on screen after the user started typing."""
        window = self._window(4)
        assert UlauncherWindow._handle_grid_navigation(window, keyname, "fi", has_modifier=False) is False
        window.results_view.go_left.assert_not_called()
        window.results_view.go_right.assert_not_called()

    @pytest.mark.parametrize("keyname", ["Left", "Right"])
    def test_ctrl_and_alt_combinations_stay_with_the_entry(self, keyname: str) -> None:
        window = self._window(4)
        assert UlauncherWindow._handle_grid_navigation(window, keyname, "", has_modifier=True) is False
        window.results_view.go_left.assert_not_called()
        window.results_view.go_right.assert_not_called()

    def test_shift_tab_still_belongs_to_the_grid(self) -> None:
        """Shift is not a blocking modifier: Shift+Tab arrives as ISO_Left_Tab."""
        window = self._window(4)
        assert UlauncherWindow._handle_grid_navigation(window, "ISO_Left_Tab", "", has_modifier=False) is True
        window.results_view.go_left.assert_called_once_with()

    def test_a_list_never_takes_the_key(self) -> None:
        assert UlauncherWindow._handle_grid_navigation(self._window(1), "Left", "", has_modifier=False) is False

    def test_unrelated_keys_fall_through(self) -> None:
        assert UlauncherWindow._handle_grid_navigation(self._window(4), "Up", "", has_modifier=False) is False


class TestResultsViewGridRender:
    """Rendering the frequent apps as a grid (builds real tile widgets)."""

    @pytest.fixture(autouse=True)
    def _no_scroll(self, mocker: MockerFixture) -> None:
        mocker.patch("ulauncher.ui.grid_result_widget.GridResultWidget.scroll_to_focus")
        mocker.patch("ulauncher.ui.result_widget.ResultWidget.scroll_to_focus")

    @staticmethod
    def _view(layout: str = "grid", columns: int = 4, icon_size: int = 48, base_width: int = 750) -> ResultsView:
        settings = MagicMock()
        settings.get_jump_keys.return_value = ["1", "2", "3", "4", "5", "6", "7", "8"]
        settings.recent_apps_layout = layout
        settings.recent_apps_grid_columns = columns
        settings.recent_apps_grid_icon_size = icon_size
        settings.recent_apps_grid_labels = "name-and-shortcut"
        settings.base_width = base_width
        return ResultsView(settings, lambda *_: None, lambda *_: None)

    @staticmethod
    def _update(count: int, is_home: bool = True) -> ResultsUpdate:
        results = [Result(name=f"app{i}") for i in range(count)]
        return results_update(results, Query(None, ""), None, False, is_home)

    def test_home_results_render_as_a_grid(self) -> None:
        view = self._view()
        view.render(self._update(6))
        assert view.columns == 4
        assert len(view._widgets) == 6
        grid = view._box.get_children()[0]
        assert isinstance(grid, Gtk.Grid)

    def test_partial_last_row_is_padded_to_keep_column_widths(self) -> None:
        view = self._view()
        view.render(self._update(6))
        grid = cast("Any", view._box.get_children()[0])
        assert len(grid.get_children()) == 6 + 2  # 2 filler cells

    def test_full_last_row_is_not_padded(self) -> None:
        view = self._view()
        view.render(self._update(8))
        grid = cast("Any", view._box.get_children()[0])
        assert len(grid.get_children()) == 8

    def test_search_results_stay_a_list(self) -> None:
        view = self._view()
        view.render(self._update(6, is_home=False))
        assert view.columns == 1
        assert not any(isinstance(child, Gtk.Grid) for child in view._box.get_children())

    def test_list_layout_setting_keeps_home_results_a_list(self) -> None:
        view = self._view(layout="list")
        view.render(self._update(6))
        assert view.columns == 1
        assert not any(isinstance(child, Gtk.Grid) for child in view._box.get_children())

    def test_zero_columns_setting_falls_back_to_one(self) -> None:
        view = self._view(columns=0)
        view.render(self._update(3))
        assert view.columns == 1

    def test_switching_from_grid_to_list_replaces_instead_of_appending(self) -> None:
        view = self._view()
        view.render(self._update(4))
        assert view.columns == 4
        # an append for a different (searching) query must not drop list rows into the grid
        append = results_update([Result(name="searched")], Query(None, "q"), None, True, False)
        view.render(append)
        assert view.columns == 1
        assert len(view._widgets) == 1

    def test_single_column_grid_still_replaces_instead_of_appending(self) -> None:
        """columns == 1 for a one-column grid, so the append guard cannot key off the count."""
        view = self._view(columns=1)
        view.render(self._update(3))
        assert view.columns == 1
        assert view._is_grid
        append = results_update([Result(name="searched")], Query(None, "q"), None, True, False)
        view.render(append)
        assert not view._is_grid
        assert len(view._widgets) == 1
        assert not any(isinstance(child, Gtk.Grid) for child in view._box.get_children())

    @pytest.mark.parametrize(
        ("base_width", "icon_size", "columns", "expected"),
        [
            pytest.param(750, 48, 4, 4, id="default_fits"),
            pytest.param(540, 128, 12, 3, id="drops_columns_that_cannot_fit"),
            pytest.param(540, 128, 2, 2, id="never_adds_columns"),
            # 4 tiles of 120px need 512 of the 540 available, so none may be dropped
            pytest.param(540, 120, 4, 4, id="keeps_columns_that_only_just_fit"),
            pytest.param(540, 48, 9, 9, id="exact_fit_is_kept"),
            pytest.param(540, 48, 10, 9, id="one_column_over_is_dropped"),
        ],
    )
    def test_columns_are_capped_by_the_window_width(
        self, base_width: int, icon_size: int, columns: int, expected: int
    ) -> None:
        view = self._view(columns=columns, icon_size=icon_size, base_width=base_width)
        view.render(self._update(12))
        assert view.columns == expected
        assert view.columns * (icon_size + TILE_EXTRA_WIDTH) <= base_width


class TestResultsViewSelection:
    """Selection logic used across streamed replace/append batches."""

    @pytest.fixture
    def view(self) -> ResultsView:
        return ResultsView(cast("Any", MagicMock()), cast("Any", MagicMock()), cast("Any", MagicMock()))

    def test_select_marks_user_selected(self, view: ResultsView) -> None:
        view._widgets = cast("Any", [_named_widget("a"), _named_widget("b")])
        view.select(1)
        assert view._index == 1
        assert view._user_selected is True

    def test_apply_selection_uses_default_name_without_marking_user_selected(self, view: ResultsView) -> None:
        view._widgets = cast("Any", [_named_widget("a"), _named_widget("keep"), _named_widget("b")])
        view._apply_selection("keep", None)
        assert view._index == 1
        assert view._user_selected is False

    def test_apply_selection_preserves_user_pick(self, view: ResultsView) -> None:
        view._widgets = cast("Any", [_named_widget("a"), _named_widget("keep"), _named_widget("b")])
        view._user_selected = True
        previous = cast("Any", MagicMock(name="prev"))
        previous.name = "keep"
        view._apply_selection(None, previous)
        assert view._index == 1
        assert view._user_selected

    def test_apply_selection_falls_back_when_user_pick_gone(self, view: ResultsView) -> None:
        view._widgets = cast("Any", [_named_widget("a"), _named_widget("b")])
        view._user_selected = True
        previous = cast("Any", MagicMock(name="prev"))
        previous.name = "gone"
        view._apply_selection("a", previous)
        assert view._index == 0
        assert not view._user_selected


class TestResultsViewStreaming:
    """End-to-end render of streamed replace/append batches (builds real result widgets)."""

    @pytest.fixture(autouse=True)
    def _no_scroll(self, mocker: MockerFixture) -> None:
        mocker.patch("ulauncher.ui.result_widget.ResultWidget.scroll_to_focus")

    @pytest.fixture
    def view(self) -> ResultsView:
        settings = MagicMock()
        no_jump_keys: list[str] = []
        settings.get_jump_keys.return_value = no_jump_keys
        return ResultsView(settings, lambda *_: None, lambda *_: None)

    @staticmethod
    def _update(
        names: list[str], query: str = "q", selected_name: str | None = None, append: bool = False
    ) -> ResultsUpdate:
        return results_update([Result(name=name) for name in names], Query(None, query), selected_name, append)

    def test_replace_preserves_user_pick_within_same_query(self, view: ResultsView) -> None:
        view.render(self._update(["a", "b", "c"]))
        view.go_down()  # user picks "b"
        # a later draft of the same query reorders the list; "b" is still present
        view.render(self._update(["x", "a", "b", "c"]))
        active = view.get_active_result()
        assert active is not None
        assert active.name == "b"

    def test_append_grows_list_and_keeps_selection(self, view: ResultsView) -> None:
        view.render(self._update(["a", "b"]))
        view.go_down()  # "b"
        view.render(self._update(["c", "d"], append=True))
        assert len(view._widgets) == 4
        active = view.get_active_result()
        assert active is not None
        assert active.name == "b"

    def test_new_query_resets_user_selection(self, view: ResultsView) -> None:
        view.render(self._update(["a", "b"], query="q1"))
        view.go_down()
        view.render(self._update(["a", "b"], query="q2"))
        assert view._user_selected is False
        assert view._index == 0
