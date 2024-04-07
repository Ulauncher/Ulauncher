from typing import Any

_instances: Any = {}


def get_instance(supercls, cls, *args, **kwargs):
    if cls not in _instances:
        _instances[cls] = supercls.__call__(*args, **kwargs)
    return _instances[cls]


# Use with metaclass=Singleton (not possible when inheriting from Gtk classes for example)
class Singleton(type):

    def __call__(cls, *args, **kwargs):
        return get_instance(super(), cls, *args, **kwargs)
