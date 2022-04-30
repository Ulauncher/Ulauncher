# See https://github.com/python/typeshed/issues/3500
# Ubuntu Bionic only has Py3.6, and there are no system packages for typing_extensions or mypy_extensions
# In Python>=3.8 we could just do "from typing import TypedDict"
# pylint: disable=unused-import


def _TypedDict(*args, **kw):
    pass


try:
    from mypy_extensions import TypedDict
except ImportError:
    TypedDict = _TypedDict
