from __future__ import annotations

from ulauncher import paths
from ulauncher.internals.result import Result


class CalcResult(Result):
    icon = f"{paths.ASSETS}/icons/calculator.png"
    result: str | None = None
