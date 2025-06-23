# ruff: noqa: F401
from ulauncher.api.extension import Extension
from ulauncher.internals.result import ActionMetadata, Result


class ExtensionResult(Result):
    pass


class ExtensionSmallResult(Result):
    compact = True
