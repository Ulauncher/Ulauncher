from ulauncher.utils.version import _valid_range, satisfies


class TestVersion:
    def test_valid_range(self) -> None:
        assert _valid_range("1.0")
        assert _valid_range("1.x")
        assert _valid_range("~1.x")
        assert _valid_range("^1.x")
        assert _valid_range("1.x.0")
        assert _valid_range("1.2.x")
        assert not _valid_range(">=1.2.x")  # Valid in semver, but don't want to support this
        assert _valid_range("1 - 2")
        assert _valid_range("1.3 - 2")
        assert not _valid_range("2 - 1")
        assert not _valid_range("1-2")  # Invalid hyphen range format (incompatible with semver library)
        assert not _valid_range("1||2")  # Valid in semver, but don't want to support this

    def test_satisfies(self) -> None:
        assert satisfies("1.5", "1")
        assert satisfies("1.5", "1.x")
        assert satisfies("1.5", "1.0")
        assert satisfies("1.5", "1.5")
        assert not satisfies("1.5", "1.6")
        assert satisfies("1.5", "1.5 - 1.5")
        assert satisfies("1.5", "1 - 1.5")
        assert not satisfies("1.5", "1 - 1.4")
        assert satisfies("1.5", "1.0 - 2")
        assert satisfies("2.3", "2 - 3.0")
        assert satisfies("2.3", "2 - 2.3")
        assert not satisfies("2.3", "2 - 2.2")
