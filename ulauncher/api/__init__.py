from ulauncher.api.extension import Extension  # noqa: F401
from ulauncher.api.result import Result


class ExtensionResult(Result):
    pass


class ExtensionSmallResult(Result):
    compact = True
