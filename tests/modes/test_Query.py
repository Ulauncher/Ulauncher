from ulauncher.modes.Query import Query


class TestQuery:

    def test_get_keyword(self):
        assert Query('kw arg').get_keyword() == 'kw'
        assert Query('kw').get_keyword() == 'kw'
        assert not Query('').get_keyword()

    def test_get_argument(self):
        assert Query('kw arg text').get_argument() == 'arg text'
        assert not Query('kw').get_argument()
        assert not Query('').get_argument()
