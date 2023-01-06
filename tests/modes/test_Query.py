from ulauncher.api.shared.query import Query


class TestQuery:
    def test_keyword(self):
        assert Query("kw arg").keyword == "kw"
        assert Query("kw").keyword == "kw"
        assert not Query("").keyword

    def test_argument(self):
        assert Query("kw arg text").argument == "arg text"
        assert not Query("kw").argument
        assert not Query("").argument

    def test_get_keyword(self):
        assert Query("kw arg").get_keyword() == "kw"
        assert Query("kw").get_keyword() == "kw"
        assert not Query("").get_keyword()

    def test_get_argument(self):
        assert Query("kw arg text").get_argument() == "arg text"
        assert not Query("kw").get_argument()
        assert not Query("").get_argument()
