from typing import cast
from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture

from ulauncher.internals.query import Query
from ulauncher.internals.result import Result
from ulauncher.ui.result_widget import ResultWidget


class TestResultWidget:
    @pytest.fixture(autouse=True)
    def scroll_to_focus(self, mocker: MockerFixture) -> MagicMock:
        return mocker.patch("ulauncher.ui.result_widget.ResultWidget.scroll_to_focus")

    def test_descr(self) -> None:
        assert len(ResultWidget(Result(), 0, Query("", None)).text_container.get_children()) == 1
        res = Result(description="descr")
        assert len(ResultWidget(res, 0, Query("", None)).text_container.get_children()) == 2
        res = Result(description="descr", compact=True)
        assert len(ResultWidget(res, 0, Query("", None)).text_container.get_children()) == 1

    def test_select(self) -> None:
        result_wgt = ResultWidget(Result(), 0, Query("query", None))
        style = result_wgt.item_box.get_style_context()
        assert "selected" not in style.list_classes()
        result_wgt.select()
        assert "selected" in style.list_classes()
        result_wgt.deselect()
        assert "selected" not in style.list_classes()

    def test_shortcut(self) -> None:
        result_wgt = ResultWidget(Result(), 0, Query("query", None))
        assert result_wgt.shortcut_label.get_text() == "Alt+1"
        result_wgt.set_index(2)
        assert result_wgt.shortcut_label.get_text() == "Alt+3"

    def test_wrap__name_and_description_labels_wrap_instead_of_ellipsizing(self) -> None:
        from gi.repository import Gtk, Pango

        res = Result(name="long name", description="long descr", wrap=True)
        widget = ResultWidget(res, 0, Query("", None))

        name_label = cast("Gtk.Label", widget.title_box.get_children()[0])
        descr_label = cast("Gtk.Label", widget.text_container.get_children()[1])
        for label in (name_label, descr_label):
            assert label.get_line_wrap()
            assert label.get_ellipsize() == Pango.EllipsizeMode.NONE

    def test_wrap__defaults_to_single_ellipsized_line(self) -> None:
        from gi.repository import Gtk, Pango

        res = Result(name="long name", description="long descr")
        widget = ResultWidget(res, 0, Query("", None))

        name_label = cast("Gtk.Label", widget.title_box.get_children()[0])
        descr_label = cast("Gtk.Label", widget.text_container.get_children()[1])
        for label in (name_label, descr_label):
            assert not label.get_line_wrap()
            assert label.get_ellipsize() == Pango.EllipsizeMode.MIDDLE

    def test_wrap__highlighting_is_skipped(self) -> None:
        from gi.repository import Gtk

        res = Result(name="wrapped name", wrap=True, highlightable=True)
        widget = ResultWidget(res, 0, Query("wrap", None))

        # highlighting would split the name over multiple labels, which cannot wrap as one paragraph
        children = widget.title_box.get_children()
        assert len(children) == 1
        assert cast("Gtk.Label", children[0]).get_text() == "wrapped name"
        assert not any("item-highlight" in c.get_style_context().list_classes() for c in children)
