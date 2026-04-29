from ulauncher.utils.lru_cache import lru_cache


def test_lru_cache_without_parentheses_preserves_caching() -> None:
    calls = 0

    @lru_cache
    def square(value: int) -> int:
        nonlocal calls
        calls += 1
        return value * value

    assert square(4) == 16
    assert square(4) == 16
    assert square.cache_info().hits == 1  # type: ignore[attr-defined]
    assert calls == 1


def test_lru_cache_supports_typed_keyword_argument() -> None:
    @lru_cache(maxsize=None, typed=True)
    def stringify(value: object) -> str:
        return repr(value)

    assert stringify(1) == "1"
    assert stringify(True) == "True"
    assert stringify.cache_info().misses == 2  # type: ignore[attr-defined]
    assert stringify.cache_info().currsize == 2  # type: ignore[attr-defined]
