from typing import Any  # noqa: N999

from ulauncher.api._deprecation import warn_legacy_api
from ulauncher.internals.result import Result


class ExtensionSmallResultItem(Result):
    compact = True

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        warn_legacy_api("ExtensionSmallResultItem", "Use `ulauncher.api.Result(compact=True)` instead.")
        super().__init__(*args, **kwargs)
