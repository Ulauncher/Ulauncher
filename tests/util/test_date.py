from ulauncher.util.date import iso_to_datetime


def test_iso_to_datetime():
    assert str(iso_to_datetime('2017-05-01T07:30:39Z')) == '2017-05-01 07:30:39'
