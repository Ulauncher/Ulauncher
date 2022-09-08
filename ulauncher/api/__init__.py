# flake8: noqa
# pylint: disable=unused-import
from ulauncher.api.extension import Extension
from ulauncher.api.result import Result


class ExtensionResult(Result):
    pass


class ExtensionSmallResult(Result):
    compact = True
