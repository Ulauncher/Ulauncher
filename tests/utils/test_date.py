from ulauncher.utils.date import iso_to_datetime


def test_iso_to_datetime():
    assert str(iso_to_datetime('2017-05-01T07:30:39Z')) == '2017-05-01 07:30:39'


def test_iso_to_datetime__with_timezone():
    assert str(iso_to_datetime('2019-01-04T16:41:24+0200', False)) == '2019-01-04 16:41:24+02:00'
