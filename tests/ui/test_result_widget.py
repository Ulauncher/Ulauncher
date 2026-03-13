from unittest.mock import MagicMock

import pytest
from gi.repository import Gtk, Pango
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

    def test_multiline_descr(self) -> None:
        q = Query("", None)
        res = Result(description="line one\nline two", multiline=True)
        widget = ResultWidget(res, 0, q)
        children = widget.text_container.get_children()
        assert len(children) == 2
        descr_label = children[1]
        assert descr_label.get_line_wrap()
        assert descr_label.get_line_wrap_mode() == Pango.WrapMode.WORD_CHAR
        assert descr_label.get_ellipsize() == Pango.EllipsizeMode.NONE
        assert widget.text_container.get_valign() == Gtk.Align.START

    def test_non_multiline_descr_ellipsizes(self) -> None:
        q = Query("", None)
        res = Result(description="a very long description")
        widget = ResultWidget(res, 0, q)
        descr_label = widget.text_container.get_children()[1]
        assert not descr_label.get_line_wrap()
        assert descr_label.get_ellipsize() == Pango.EllipsizeMode.MIDDLE

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
