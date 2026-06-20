from __future__ import annotations

from types import SimpleNamespace
from typing import Any, cast
from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture

from ulauncher.internals.query import Query
from ulauncher.internals.result import Result
from ulauncher.internals.results_update import ResultsUpdate, results_update
from ulauncher.ui.results_view import ResultsView


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
        view = ResultsView(cast("Any", MagicMock()), cast("Any", MagicMock()))
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
        view = ResultsView(cast("Any", MagicMock()), cast("Any", MagicMock()))
        view.select(2)
        view.go_up()
        view.go_down()
        assert view.get_active_result() is None
        assert not view.has_results


class TestResultsViewSelection:
    """Selection logic used across streamed replace/append batches."""

    @pytest.fixture
    def view(self) -> ResultsView:
        return ResultsView(cast("Any", MagicMock()), cast("Any", MagicMock()))

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
        return ResultsView(settings, lambda *_: None)

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
