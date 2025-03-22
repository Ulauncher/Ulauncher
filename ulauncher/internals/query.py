from __future__ import annotations


class Query:
    """
    argument should be None if there is no space after the keyword.
    If there is only a space after, argument should be an empty string
    """

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
        """
        If the query has an argument that is not None it counts as active
        If the query has a keyword and a space after the keyword, it counts as active because
        then the argument is an empty string
        """
        return self.argument is not None

    def get_keyword(self) -> str | None:
        # TODO: Add deprecation warning
        return self.keyword

    def get_argument(self, default: str | None = None) -> str | None:
        # TODO: Add deprecation warning
        return self.argument or default

    @staticmethod
    def parse_str(query_str: str) -> Query:
        """Create a Query object from a string (assuming first word is the keyword)"""
        argument: str | None = None
        components = query_str.split(" ", 1)
        if len(components) > 1:
            # argument will be an empty string if there is only a space after the keyword (see is_active property)
            argument = components[1]
        return Query(components[0], argument)
