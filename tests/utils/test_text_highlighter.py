from functools import partial

from ulauncher.utils.text_highlighter import highlight_text


def test_highlight_text():
    hl = partial(highlight_text, open_tag='<i>', close_tag='</i>')
    assert hl('fifox', 'Firefox') == '<i>Fi</i>re<i>fox</i>'
    assert hl('hell wo', 'hello world') == '<i>hell</i>o<i> wo</i>rld'
    assert hl('ttesti', 'testik_ls-ttestk') == '<i>testi</i>k_ls-ttestk'
    assert hl('dome', 'Documents') == '<i>Do</i>cu<i>me</i>nts'
    assert hl('e tom', 'São tomé & príncipe') == 'São<i> tom</i>é & príncip<i>e</i>'
