# flake8: noqa
# pylint: disable=unused-import
from ulauncher.api.extension import Extension
from ulauncher.api.extension_result import ExtensionResult


class ExtensionSmallResult(ExtensionResult):
    compact = True
