from __future__ import annotations


class Query:
    """argument is None when nothing follows the keyword, or "" when only a space follows."""

    keyword: str | None
    argument: str | None

    def __init__(self, keyword: str | None, argument: str | None) -> None:
        super().__init__()
        self.keyword = keyword
        self.argument = argument

    def __str__(self) -> str:
        if self.keyword and self.argument is not None:
            return f"{self.keyword} {self.argument}"
        return self.keyword or self.argument or ""

    @property
    def is_active(self) -> bool:
        # A trailing space after the keyword sets argument to "", which still counts as active.
        return self.argument is not None
