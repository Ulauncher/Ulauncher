import time
from ulauncher.utils.fuzzy_search import get_matching_blocks, get_score


def test_get_matching_indexes():
    assert get_matching_blocks('thfima', 'Thunar File Manager') == [(0, 'Th'), (7, 'Fi'), (12, 'Ma')]


def test_get_score():
    assert get_score('calc', 'Contacts') < get_score('calc', 'LibreOffice Calc')
    assert get_score('clac', 'LibreOffice Calc') < get_score('clac', 'Calc')
    assert get_score('pla', 'Pycharm') < get_score('pla', 'Google Play Music')
    assert get_score('', 'LibreOffice Calc') == 0
    assert get_score('0', 'LibreOffice Calc') == 0


def xtest_speed():
    t0 = time.time()
    for _ in range(1000):
        get_score('fiwebro', 'Firefox Web Browser')
    print('time for get_score:', (time.time() - t0))
    assert 0
