from ulauncher.ui.windows.preferences.utils.ext_utils import autofmt_pango_code_block


class TestAutofmtPangoCodeBlock:
    def test_returns_text_unchanged_when_no_code_tags(self) -> None:
        text = "Hello world"
        assert autofmt_pango_code_block(text) == "Hello world"

    def test_converts_code_tags_to_pango_markup(self) -> None:
        text = "Run <code>pip install</code> to install"
        result = autofmt_pango_code_block(text)
        assert result == 'Run <span face="monospace" bgcolor="#90600050">pip install</span> to install'
