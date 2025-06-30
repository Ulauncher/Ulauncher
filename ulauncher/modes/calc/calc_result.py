from __future__ import annotations

from decimal import Decimal

from ulauncher.config import paths
from ulauncher.internals.result import Result


class CalcResult(Result):
    icon = f"{paths.ASSETS}/icons/calculator.png"
    error = ""

    def __init__(self, result: str | None = None, error: str = "Unknown error") -> None:
        super().__init__(result=result, error=error)
        self.name = f"{Decimal(self.result):n}" if self.result is not None else "Error!"
        self.description = "Enter to copy to the clipboard" if self.result is not None else error
