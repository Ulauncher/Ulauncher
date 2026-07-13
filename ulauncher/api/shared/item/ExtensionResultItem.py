from __future__ import annotations  # noqa: N999

from typing import Any

from ulauncher.api import Result
from ulauncher.api._deprecation import warn_legacy_api


class ExtensionResultItem(Result):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        warn_legacy_api("ExtensionResultItem", "Use `ulauncher.api.Result` instead.")
        super().__init__(*args, **kwargs)

    def get_keyword(self) -> str:
        return self.keyword

    def get_name(self) -> str:
        return self.name

    def get_icon(self) -> str | None:
        return self.icon
