from __future__ import annotations

from ulauncher import paths
from ulauncher.internals.result import Result

calc_icon = f"{paths.ASSETS}/icons/calculator.png"


class CalcResult(Result):
    icon: str = calc_icon
    result: str = ""
    actions = {"copy": {"name": "Copy to clipboard", "icon": "edit-copy"}}


class CalcCompletionResult(Result):
    icon: str = calc_icon
    completion: str = ""
    actions = {"complete": {"name": "Complete expression", "icon": "go-next"}}


class CalcErrorResult(Result):
    name: str = "Error!"
    description: str = "Invalid expression"
    icon: str = calc_icon
