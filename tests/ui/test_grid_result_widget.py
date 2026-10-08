from __future__ import annotations

from typing import Any, cast
from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture

from ulauncher.internals.query import Query
from ulauncher.internals.result import Result
from ulauncher.ui.grid_result_widget import MAX_ICON_SIZE, MIN_ICON_SIZE, GridResultWidget

JUMP_KEYS = ["1", "2", "3", "4", "5"]


def noop(*_args: object) -> None:
    pass


def _widget(**kwargs: Any) -> GridResultWidget:
    result = kwargs.pop("result", Result(name="Firefox Web Browser"))
    return GridResultWidget(result, kwargs.pop("index", 0), Query("", None), noop, noop, JUMP_KEYS, **kwargs)


class TestGridResultWidget:
    @pytest.fixture(autouse=True)
    def scroll_to_focus(self, mocker: MockerFixture) -> MagicMock:
        return mocker.patch("ulauncher.ui.grid_result_widget.GridResultWidget.scroll_to_focus")

    @pytest.mark.parametrize(
        ("labels", "has_name", "has_shortcut"),
        [
            ("none", False, False),
            ("name", True, False),
            ("shortcut", False, True),
            ("name-and-shortcut", True, True),
        ],
    )
    def test_labels(self, labels: str, has_name: bool, has_shortcut: bool) -> None:
        widget = _widget(labels=cast("Any", labels))
        assert (widget.name_label is not None) is has_name
        assert (widget.shortcut_label is not None) is has_shortcut
        container = widget.item_box.get_children()[0]
        expected_children = 1 + int(has_name) + int(has_shortcut)  # icon + optional labels
        assert len(cast("Any", container).get_children()) == expected_children

    def test_name_is_not_highlighted(self) -> None:
        # the grid only shows on an empty query, so the name is one plain label
        widget = _widget(labels="name")
        assert widget.name_label is not None
        assert widget.name_label.get_text() == "Firefox Web Browser"

    def test_name_wraps_instead_of_ellipsizing_the_middle(self) -> None:
        from gi.repository import Pango

        widget = _widget(labels="name")
        assert widget.name_label is not None
        assert widget.name_label.get_line_wrap()
        assert widget.name_label.get_ellipsize() == Pango.EllipsizeMode.END

    def test_shortcut(self) -> None:
        widget = _widget()
        assert widget.shortcut_label is not None
        assert widget.shortcut_label.get_text() == "Alt+1"
        widget.set_index(2)
        assert widget.shortcut_label.get_text() == "Alt+3"

    def test_set_index_without_a_shortcut_label_is_a_noop(self) -> None:
        widget = _widget(labels="name")
        widget.set_index(3)
        assert widget.index == 3

    def test_select(self) -> None:
        widget = _widget()
        style = widget.item_box.get_style_context()
        assert "selected" not in style.list_classes()
        widget.select()
        assert "selected" in style.list_classes()
        widget.deselect()
        assert "selected" not in style.list_classes()

    def test_style_classes_reuse_the_list_item_classes(self) -> None:
        """Tiles must keep the .item-* classes so that themes color them without any changes."""
        widget = _widget()
        assert {"item-frame", "grid-item-frame"} <= set(widget.get_style_context().list_classes())
        assert {"item-box", "grid-item-box"} <= set(widget.item_box.get_style_context().list_classes())
        assert widget.name_label is not None
        assert {"item-name", "item-text", "grid-item-name"} <= set(widget.name_label.get_style_context().list_classes())
        assert widget.shortcut_label is not None
        assert {"item-shortcut", "item-text", "grid-item-shortcut"} <= set(
            widget.shortcut_label.get_style_context().list_classes()
        )

    @pytest.mark.parametrize(
        ("requested", "expected"),
        [(4, MIN_ICON_SIZE), (48, 48), (999, MAX_ICON_SIZE)],
    )
    def test_icon_size_is_clamped(self, requested: int, expected: int) -> None:
        widget = _widget(icon_size=requested)
        icon = cast("Any", widget.item_box.get_children()[0]).get_children()[0]
        assert icon.get_size_request() == (expected, expected)

    def test_click_activates_its_own_index(self, mocker: MockerFixture) -> None:
        on_activate = mocker.MagicMock()
        widget = GridResultWidget(Result(name="a"), 2, Query("", None), noop, on_activate, JUMP_KEYS)
        widget.on_click(widget)
        on_activate.assert_called_once_with(2, False)

    @pytest.mark.parametrize("scale_factor", [1, 2])
    def test_icon_surface_is_requested_for_the_monitor_scale(self, mocker: MockerFixture, scale_factor: int) -> None:
        """The size request stays logical px; only the surface is loaded at the scaled size."""
        import cairo

        # Gtk.Image.set_from_surface rejects a mock, so hand it a real (empty) surface
        load_icon_surface = mocker.patch(
            "ulauncher.ui.grid_result_widget.load_icon_surface",
            return_value=cairo.ImageSurface(cairo.FORMAT_ARGB32, 1, 1),
        )
        mocker.patch("ulauncher.ui.grid_result_widget.GridResultWidget.get_scale_factor", return_value=scale_factor)

        widget = _widget(result=Result(name="a", icon="firefox"), icon_size=48)

        load_icon_surface.assert_called_once_with("firefox", 48, scale_factor)
        icon = cast("Any", widget.item_box.get_children()[0]).get_children()[0]
        assert icon.get_size_request() == (48, 48)
