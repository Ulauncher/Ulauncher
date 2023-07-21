from __future__ import annotations

from decimal import Decimal

from ulauncher.api.result import Result
from ulauncher.api.shared.action.CopyToClipboardAction import CopyToClipboardAction
from ulauncher.config import PATHS


class CalcResult(Result):
    icon = f"{PATHS.ASSETS}/icons/calculator.png"

    def __init__(self, result: Decimal | None = None, error: str = "Unknown error"):
        super().__init__(result=result, error=error)
        self.name = f"{Decimal(self.result):n}" if self.result is not None else "Error!"
        self.description = "Enter to copy to the clipboard" if self.result is not None else error

    def on_activation(self, *_):
        if self.result is not None:
            return CopyToClipboardAction(str(self.result))

        return True
