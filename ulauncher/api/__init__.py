# ruff: noqa: F401
from ulauncher.api.extension import Extension
from ulauncher.internals import effects
from ulauncher.internals.result import Result


class ExtensionResult(Result):
    pass


class ExtensionSmallResult(Result):
    compact = True
