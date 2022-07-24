import json
import logging
from copy import deepcopy
from pathlib import Path
from typing import Any, cast, Dict, List, Tuple, Type, TypeVar


def filter_recursive(data, blacklist):
    if isinstance(data, dict):
        return {k: filter_recursive(v, blacklist) for k, v in data.items() if v not in blacklist}
    if isinstance(data, list):
        return [filter_recursive(v, blacklist) for v in data]
    return data


_file_instances: Dict[Tuple[Path, Type], "JsonData"] = {}
logger = logging.getLogger()
# Optimally use "TypeVar('T', bound=JsonData"), but it requires py3.7 see https://stackoverflow.com/a/63237226/633921
T = TypeVar("T", bound="JsonData")


"""
JsonData

This is an simpler alternative to dataclasses (not supported in py3.6/ubuntu18.04)
It's implemented using the AttrDict pattern, but it avoids self.__dict__ = self
It also has some convenient methods for loading data from json, stringifying and saving.

File paths are stored in a reference dict, because it's not part of the data.

It's important that you use the @json_data_class decorator if you use default props declared on the class.
Otherwise the defaults become effectively immutable/frozen because those properties take precedence over
the dunder-methods (__getattr__, __setattr__ and __delattr__)
This is also how this class allows custom methods that won't clash with the regular props

# Example use:
from ulauncher.utils.json_data import JsonData, json_data_class

@json_data_class
class Person(JsonData):
    first_name = "John"
    last_name = "Smith"

    def full_name(self):
        return self.first_name + " " + self.last_name

jw = Person(last_name="Wayne")
print(jw.full_name()) # John Wayne
jw.save_as("/path/to/file") # Save as JSON to the given path
"""


class JsonData(dict):
    __json_sort_keys__ = True
    __json_value_blacklist__: List[Any] = [[], {}, None]  # pylint: disable=dangerous-default-value

    def __init__(self, *args, **kwargs):
        super().__init__(deepcopy(getattr(self, "__default_props__", {})))
        self.update(*args, **kwargs)

    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{key}'") from None

    def __setattr__(self, key, value):
        self[key] = value

    def __delattr__(self, name):
        del self[name]

    def __dir__(self):  # For IDE autocompletion
        return dir(type(self)) + list(self.keys())

    # Make sure everything flows hrough __setitem__ except __default_props__
    def update(self, *args, **kwargs):
        for k, v in dict(*args, **kwargs).items():
            self[k] = v

    @classmethod
    def new_from_file(cls: Type[T], path) -> T:
        data = {}
        file_path = Path(path).resolve()
        key = (file_path, cls)
        if key not in _file_instances and file_path.is_file():
            try:
                data = json.loads(file_path.read_text())
            except Exception as e:
                logger.error("Error '%s' opening JSON file %s: %s", type(e).__name__, file_path, e)
                logger.warning("Ignoring invalid JSON file (%s)", file_path)

        instance = _file_instances.get(key, cls())
        instance.update(data)
        _file_instances[key] = instance
        return cast(T, instance)

    def stringify(self, indent=None, sort_keys=True):
        # When serializing to JSON, filter out common empty default values like None, empty list or dict
        # These are needed in Python for typing consistency and hints, but they are not actual data
        data = filter_recursive(self, self.__json_value_blacklist__)
        return json.dumps(data, indent=indent, sort_keys=sort_keys)

    def save(self, *args, **kwargs) -> bool:
        self.update(*args, **kwargs)
        file_path = next((key[0] for key, inst in _file_instances.items() if inst == self), None)

        return self.save_as(file_path)

    def save_as(self, path) -> bool:
        """Save self to file path"""
        file_path = Path(path).resolve()
        if file_path:
            try:
                # Ensure parent dir first
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.write_text(self.stringify(indent=2, sort_keys=self.__json_sort_keys__))
                return True
            except Exception as e:
                logger.error("Error '%s' writing to JSON file %s: %s.", type(e).__name__, file_path, e)
        return False


def json_data_class(cls):
    # Perserve the class order
    cls.__json_sort_keys__ = False
    # Moves the class props to __default_props__ (JsonData handles this)
    if not hasattr(cls, "__default_props__"):
        cls.__default_props__ = {}
    props = {k: v for k, v in vars(cls).items() if (not k.startswith("__") and not callable(getattr(cls, k)))}
    for prop, value in props.items():
        cls.__default_props__[prop] = value
        delattr(cls, prop)

    return cls
