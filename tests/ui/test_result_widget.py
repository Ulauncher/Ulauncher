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
