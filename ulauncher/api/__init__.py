from ulauncher.api.extension import Extension  # noqa: F401
from ulauncher.internals.result import Result


class ExtensionResult(Result):
    pass


class ExtensionSmallResult(Result):
    compact = True
