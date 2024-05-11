from __future__ import annotations


class Query(str):
    # Splits to a list with the keyword and argument and pad with empty strings
    def _get_components(self) -> list[str]:
        components = self.split(None, 1)
        return components + [""] * (2 - len(components))

    @property
    def keyword(self) -> str:
        return self._get_components()[0]

    @property
    def argument(self) -> str:
        return self._get_components()[1]

    def get_keyword(self) -> str:
        return self.keyword

    def get_argument(self, default: str | None = None) -> str | None:
        return self.argument or default
