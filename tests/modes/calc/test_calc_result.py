from typing import Any
from unittest.mock import MagicMock

import pytest

from ulauncher.internals.query import Query
from ulauncher.modes.calc.calc_result import CalcResult


class TestCalcResult:
    @pytest.fixture
    def copy_action(self, mocker: MagicMock) -> Any:
        return mocker.patch("ulauncher.modes.calc.calc_result.actions.copy")

    def test_get_name(self) -> None:
        assert CalcResult(result="52").name == "52"
        assert CalcResult("42").name == "42"
        assert CalcResult(error="message").name == "Error!"

    def test_get_description(self) -> None:
        assert CalcResult(result="52").description == "Enter to copy to the clipboard"
        assert CalcResult(error="message").description == "message"

    def test_on_activation(self, copy_action: MagicMock) -> None:
        item = CalcResult(result="52")
        assert item.on_activation(Query(None, "52")) == copy_action.return_value
        copy_action.assert_called_with("52")

    def test_on_activation__error__returns_true(self, copy_action: MagicMock) -> None:
        item = CalcResult(error="message")
        assert item.on_activation(Query(None, "()")) is True
        assert not copy_action.called
