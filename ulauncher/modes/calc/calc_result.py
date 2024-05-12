from __future__ import annotations

from decimal import Decimal

from ulauncher.config import paths
from ulauncher.internals import actions
from ulauncher.internals.query import Query
from ulauncher.internals.result import Result


class CalcResult(Result):
    icon = f"{paths.ASSETS}/icons/calculator.png"

    def __init__(self, result: str | None = None, error: str = "Unknown error"):
        super().__init__(result=result, error=error)
        self.name = f"{Decimal(self.result):n}" if self.result is not None else "Error!"
        self.description = "Enter to copy to the clipboard" if self.result is not None else error

    def on_activation(self, _query: Query, _alt: bool = False) -> bool | dict[str, str]:
        if self.result is not None:
            return actions.copy(str(self.result))

        return True
