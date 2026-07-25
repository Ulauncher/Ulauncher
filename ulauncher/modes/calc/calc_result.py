from __future__ import annotations

from ulauncher import paths
from ulauncher.internals.result import Result

calc_icon = f"{paths.ASSETS}/icons/calculator.png"


class CalcResult(Result):
    icon = calc_icon
    result = ""
    actions = {"copy": {"name": "Copy to clipboard", "icon": "edit-copy"}}


class CalcCompletionResult(Result):
    icon = calc_icon
    completion = ""
    actions = {"complete": {"name": "Complete expression", "icon": "go-next"}}


class CalcErrorResult(Result):
    name = "Error!"
    description = "Invalid expression"
    icon = calc_icon
