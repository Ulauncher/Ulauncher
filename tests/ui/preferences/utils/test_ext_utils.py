import pytest

from ulauncher.modes.extensions.extension_record import ExtensionErrorData
from ulauncher.ui.preferences.utils.ext_utils import autofmt_pango_code_block, get_error_message

WEBSITE = "https://host.tld/u/r"
ISSUES = "https://tracker.tld/u/r/-/issues"
WEBSITE_LINK = f'<a href="{WEBSITE}">{WEBSITE}</a>'
ISSUES_LINK = f'<a href="{ISSUES}">{ISSUES}</a>'


class TestGetErrorMessage:
    @pytest.mark.parametrize(
        ("website_url", "issues_url", "expected_suffix"),
        [
            (WEBSITE, ISSUES, f"\n\n<small>You can report the issue: {ISSUES_LINK}</small>"),
            (WEBSITE, "", f"\n\n<small>You can report this to the author via their repository: {WEBSITE_LINK}</small>"),
            ("", "", ""),
        ],
    )
    def test_report_link_prefers_the_tracker_and_is_omitted_without_urls(
        self, website_url: str, issues_url: str, expected_suffix: str
    ) -> None:
        error = ExtensionErrorData(type="Exited", message="boom")
        expected = f"The extension exited with an error.\n\n<small>Details: boom</small>{expected_suffix}"
        assert get_error_message(error, website_url, issues_url) == expected

    def test_missing_module_links_the_issue_tracker(self) -> None:
        error = ExtensionErrorData(type="MissingModule", message="requests")
        message = get_error_message(error, WEBSITE, ISSUES)
        assert "pip3 install requests --user" in message
        assert f'report the issue: <a href="{ISSUES}">{ISSUES}</a>' in message

    def test_terminated_links_the_issue_tracker(self) -> None:
        error = ExtensionErrorData(type="Terminated")
        message = get_error_message(error, WEBSITE, ISSUES)
        assert f"You can report the issue: {ISSUES_LINK}" in message
        assert WEBSITE not in message

    def test_url_is_escaped_into_the_markup(self) -> None:
        error = ExtensionErrorData(type="Exited", message="boom")
        message = get_error_message(error, "", 'https://host.tld/?a="><b>x</b>')
        assert "<b>x</b>" not in message
        assert "&quot;&gt;&lt;b&gt;" in message


class TestAutofmtPangoCodeBlock:
    def test_returns_text_unchanged_when_no_code_tags(self) -> None:
        text = "Hello world"
        assert autofmt_pango_code_block(text) == "Hello world"

    def test_converts_code_tags_to_pango_markup(self) -> None:
        text = "Run <code>pip install</code> to install"
        result = autofmt_pango_code_block(text)
        assert result == 'Run <span face="monospace" bgcolor="#90600050">pip install</span> to install'

    def test_converts_code_tags_with_attributes_to_pango_markup(self) -> None:
        text = 'Run <code class="highlight">pip install</code> to install'
        result = autofmt_pango_code_block(text)
        assert result == 'Run <span face="monospace" bgcolor="#90600050">pip install</span> to install'
