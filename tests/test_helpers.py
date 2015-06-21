from ulauncher.helpers import string_score


def test_string_score():
    assert string_score('j', 'johnny') > 60
    assert string_score('j', 'johnny') < string_score('j', 'john')

    assert string_score('calc', 'LibreOffice Calc') > 60
    assert string_score('calc', 'LibreOffice Calc') < string_score('calc', 'Calc')
    assert string_score('libreca', 'LibreOffice Calc') > 60

    assert string_score('ie', 'LibreOffice Calc') < 40
    assert string_score('', 'LibreOffice Calc') == 0
    assert string_score('0', 'LibreOffice Calc') == 0

    assert string_score('.pdf', 'testfile.pdf') > string_score('.pdf', 'dpdf')
