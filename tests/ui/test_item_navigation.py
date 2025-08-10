from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture

from ulauncher.ui.item_navigation import ItemNavigation
from ulauncher.ui.result_widget import ResultWidget


class TestItemNavigation:
    @pytest.fixture
    def query_handler(self) -> MagicMock:
        return MagicMock()

    @pytest.fixture
    def items(self) -> list[MagicMock]:
        return [MagicMock() for _ in range(5)]

    @pytest.fixture
    def nav(self, query_handler: Any, items: list[ResultWidget]) -> ItemNavigation:
        return ItemNavigation(query_handler, items)

    @pytest.fixture(autouse=True)
    def query_history(self, mocker: MockerFixture) -> Any:
        return mocker.patch("ulauncher.ui.item_navigation.query_history")

    @pytest.fixture(autouse=True)
    def json_save(self, mocker: MockerFixture) -> Any:
        return mocker.patch("ulauncher.ui.item_navigation.json_save")

    def test_select_is_called(self, nav: ItemNavigation, items: list[MagicMock]) -> None:
        nav.select(1)
        assert nav.index == 1
        items[1].select.assert_called_once_with()

    def test_select_and_deselect_is_called(self, nav: ItemNavigation, items: list[MagicMock]) -> None:
        nav.select(1)
        nav.select(5)
        items[1].deselect.assert_called_once_with()
        items[0].select.assert_called_once_with()
        assert nav.index == 0, "First element is not selected"

    def test_go_up_from_start(self, nav: ItemNavigation, items: list[MagicMock]) -> None:
        nav.go_up()
        items[4].select.assert_called_once_with()

    def test_go_up_from_1st(self, nav: ItemNavigation, items: list[MagicMock]) -> None:
        nav.select(1)
        nav.go_up()
        items[0].select.assert_called_once_with()

    def test_go_up_from_last(self, nav: ItemNavigation, items: list[MagicMock]) -> None:
        nav.select(4)
        nav.go_up()
        items[3].select.assert_called_once_with()

    def test_go_down_from_second(self, nav: ItemNavigation, items: list[MagicMock]) -> None:
        nav.select(2)
        nav.go_down()
        items[3].select.assert_called_once_with()

    def test_go_down_from_last(self, nav: ItemNavigation, items: list[MagicMock]) -> None:
        nav.select(4)
        nav.go_down()
        items[0].select.assert_called_once_with()
