from functools import reduce
import gi
gi.require_version('GdkX11', '3.0')
# pylint: disable=wrong-import-position
from gi.repository import GdkX11

import pytest

is_display_enabled = bool(GdkX11.X11Display.get_default())


def pytest_runtest_setup(item):
    if isinstance(item, pytest.Function):
        if item.iter_markers('with_display') and not is_display_enabled:
            pytest.skip("Cannot run without a display enabled.")


class DictHasValues(dict):
    """
    DictHasValues({('foo', 'bar'): 'hello'}) == {'foo': {'bar': 'hello'}}
    """

    def __eq__(self, other):
        try:
            return all([self.find(k, other) == v for k, v in self.items()])
        except KeyError:
            return False

    def find(self, keys, other):
        if not isinstance(keys, tuple):
            keys = (keys,)
        return reduce(lambda d, key: d[key], keys, other)


setattr(pytest, 'DictHasValues', DictHasValues)


def test_DictWithValues():

    assert DictHasValues({'test': 'hello'}) == {'test': 'hello', 'other': False}
    assert DictHasValues({('test',): 'hello'}) == {'test': 'hello'}
    assert DictHasValues({('foo', 'bar'): 'hello'}) == {'foo': {'bar': 'hello', 1: 2}}
    assert DictHasValues({(1, 'bar'): 'hello'}) == {1: {'bar': 'hello'}}

    assert DictHasValues({'test': 'hello'}) != {'test': 'wrong val', 'other': False}
    assert DictHasValues({('foo', 'bar'): 'hello'}) != {'foo': None}
