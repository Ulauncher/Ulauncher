from ulauncher.api._deprecation import warn_legacy_api  # noqa: N999
from ulauncher.api.extension import Extension as _Extension

__all__ = ["Extension"]


class Extension(_Extension):
    def __init__(self) -> None:
        warn_legacy_api("Extension", "Import `Extension` from `ulauncher.api` instead.")
        super().__init__()
