from ulauncher.utils.SortedCollection import SortedCollection


def ve2no(f, *args):
    'Convert ValueError result to -1'
    try:
        return f(*args)
    except ValueError:
        return -1


def slow_index(seq, k):
    'Location of match or -1 if not found'
    for i, item in enumerate(seq):
        if item == k:
            return i
    return -1


def slow_find(seq, k):
    'First item with a key equal to k. -1 if not found'
    for item in seq:
        if item == k:
            return item
    return -1


def slow_find_le(seq, k):
    'Last item with a key less-than or equal to k.'
    for item in reversed(seq):
        if item <= k:
            return item
    return -1


def slow_find_lt(seq, k):
    'Last item with a key less-than k.'
    for item in reversed(seq):
        if item < k:
            return item
    return -1


def slow_find_ge(seq, k):
    'First item with a key-value greater-than or equal to k.'
    for item in seq:
        if item >= k:
            return item
    return -1


def slow_find_gt(seq, k):
    'First item with a key-value greater-than or equal to k.'
    for item in seq:
        if item > k:
            return item
    return -1


# pylint: disable=too-many-statements
def test_SortedCollection():
    from random import choice
    pool = [1.5, 2, 2.0, 3, 3.0, 3.5, 4, 4.0, 4.5]
    for i in range(500):
        for n in range(6):
            s = [choice(pool) for i in range(n)]
            sc = SortedCollection(s)
            s.sort()
            for probe in pool:
                assert repr(ve2no(sc.index, probe)) == repr(slow_index(s, probe))
                assert repr(ve2no(sc.find, probe)) == repr(slow_find(s, probe))
                assert repr(ve2no(sc.find_le, probe)) == repr(slow_find_le(s, probe))
                assert repr(ve2no(sc.find_lt, probe)) == repr(slow_find_lt(s, probe))
                assert repr(ve2no(sc.find_ge, probe)) == repr(slow_find_ge(s, probe))
                assert repr(ve2no(sc.find_gt, probe)) == repr(slow_find_gt(s, probe))
            for j, item in enumerate(s):
                assert repr(item) == repr(sc[j])        # test __getitem__
                assert item in sc                       # test __contains__ and __iter__
                assert s.count(item) == sc.count(item)  # test count()
            assert len(sc) == n                         # test __len__
            assert list(map(repr, reversed(sc))) == list(map(repr, reversed(s)))    # test __reversed__
            assert list(sc.copy()) == list(sc)          # test copy()
            sc.clear()                                  # test clear()
            assert not sc

    sd = SortedCollection('The quick Brown Fox jumped'.split(), key=str.lower)
    assert sd._keys == ['brown', 'fox', 'jumped', 'quick', 'the']
    assert sd._items == ['Brown', 'Fox', 'jumped', 'quick', 'The']
    assert sd._key == str.lower
    assert repr(sd) == "SortedCollection(['Brown', 'Fox', 'jumped', 'quick', 'The'], key=lower)"
    sd.key = str.upper
    assert sd._key == str.upper
    assert len(sd) == 5
    assert list(reversed(sd)) == ['The', 'quick', 'jumped', 'Fox', 'Brown']
    for item in sd:
        assert item in sd
    for i, item in enumerate(sd):
        assert item == sd[i]
    sd.insert('jUmPeD')
    sd.insert_right('QuIcK')
    assert sd._keys == ['BROWN', 'FOX', 'JUMPED', 'JUMPED', 'QUICK', 'QUICK', 'THE']
    assert sd._items == ['Brown', 'Fox', 'jUmPeD', 'jumped', 'quick', 'QuIcK', 'The']
    assert sd.find_le('JUMPED') == 'jumped', sd.find_le('JUMPED')
    assert sd.find_ge('JUMPED') == 'jUmPeD'
    assert sd.find_le('GOAT') == 'Fox'
    assert sd.find_ge('GOAT') == 'jUmPeD'
    assert sd.find('FOX') == 'Fox'
    assert sd[3] == 'jumped'
    assert sd[3:5] == ['jumped', 'quick']
    assert sd[-2] == 'QuIcK'
    assert sd[-4:-2] == ['jumped', 'quick']
    for i, item in enumerate(sd):
        assert sd.index(item) == i
    try:
        sd.index('xyzpdq')
    except ValueError:
        pass
    else:
        assert 0, 'Oops, failed to notify of missing value'
    sd.remove('jumped')
    assert list(sd) == ['Brown', 'Fox', 'jUmPeD', 'quick', 'QuIcK', 'The']
