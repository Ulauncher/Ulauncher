from __future__ import annotations  # noqa: N999

from ulauncher.internals.result import Result


# TODO: deprecate this class. Use ulauncher.api.Result instead
class ExtensionResultItem(Result):
    def get_keyword(self) -> str:
        return self.keyword

    def get_name(self) -> str:
        return self.name

    def get_icon(self) -> str | None:
        return self.icon
