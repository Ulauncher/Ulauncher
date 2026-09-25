from __future__ import annotations

from ulauncher.internals.result import Result


def test_search_score__empty_fields__is_zero() -> None:
    assert Result(searchable=True).search_score("fire") == 0
