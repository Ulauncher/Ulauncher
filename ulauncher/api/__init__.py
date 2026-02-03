from ulauncher.api.extension import Extension
from ulauncher.internals import effects
from ulauncher.internals.result import Result

__all__ = ["Extension", "ExtensionResult", "ExtensionSmallResult", "Result", "effects"]


class ExtensionResult(Result):
    pass


class ExtensionSmallResult(Result):
    compact = True
