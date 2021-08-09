from ulauncher.utils.version_cmp import gtk_version_is_gte


def test_gtk_version_is_gte():
    # test sould pass with GTK 3.22.30
    assert gtk_version_is_gte(1, 99, 100)
    assert not gtk_version_is_gte(100, 1, 1)
    assert gtk_version_is_gte(3, 0, 0)
    assert gtk_version_is_gte(3, 22, 0)
