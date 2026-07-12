from __future__ import annotations

from ulauncher.api._deprecation import warn_legacy_api
from ulauncher.internals.query import Query as _Query

__all__ = ["Query"]


class Query(_Query):
    def get_keyword(self) -> str | None:
        warn_legacy_api("Query.get_keyword", "Use the `keyword` attribute instead.")
        return self.keyword

    def get_argument(self, default: str | None = None) -> str | None:
        warn_legacy_api("Query.get_argument", "Use the `argument` attribute instead.")
        return self.argument or default
