from ulauncher.internals.query import Query


class TestQuery:
    def test_keyword(self) -> None:
        assert Query.parse_str("kw").keyword == "kw"
        assert Query.parse_str("kw arg").keyword == "kw"
        assert Query("kw", "arg").keyword == "kw"
        assert Query("kw", None).keyword == "kw"
        assert not Query(None, None).keyword

    def test_argument(self) -> None:
        assert Query.parse_str("kw arg").argument == "arg"
        assert Query("kw", "arg").argument == "arg"
        assert not Query.parse_str("kw").argument
        assert not Query("kw", None).argument
        assert not Query(None, None).argument

    def test_is_active(self) -> None:
        assert Query.parse_str("kw arg").is_active
        assert Query.parse_str("kw ").is_active
        assert not Query.parse_str("kw").is_active
