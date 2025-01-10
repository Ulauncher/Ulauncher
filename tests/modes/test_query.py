from ulauncher.internals.query import Query


class TestQuery:
    def test_keyword(self):
        assert Query("kw arg").keyword == "kw"
        assert Query("kw").keyword == "kw"
        assert not Query("").keyword

    def test_argument(self):
        assert Query("kw arg text").argument == "arg text"
        assert not Query("kw").argument
        assert not Query("").argument
