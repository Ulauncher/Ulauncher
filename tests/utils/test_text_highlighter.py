from ulauncher.utils.text_highlighter import highlight_text as hl


def test_highlight_text():
    assert list(hl("fifox", "Firefox")) == [("Fi", True), ("re", False), ("fox", True)]
    assert list(hl("hell wo", "hello world")) == [("hell", True), ("o", False), (" wo", True), ("rld", False)]
    assert list(hl("dome", "Documents")) == [("Do", True), ("cu", False), ("me", True), ("nts", False)]
    assert list(hl("e tom", "São tomé & príncipe")) == [("São", False), (" tom", True), ("é & príncipe", False)]
    assert list(hl("date", "Date &amp; Time")) == [("Date", True), (" &amp; Time", False)]
