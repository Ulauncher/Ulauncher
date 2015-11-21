from ulauncher.utils.lcs import lcs


def test_lcs():

    assert lcs('ttest', 'test_owiefj-testji') == 'test'
    assert lcs('ttestik', 'test_owiefj-ttesti') == 'ttesti'
