import json
import logging
from copy import deepcopy
from pathlib import Path
from typing import Dict


_file_instances: Dict[Path, dict] = {}
logger = logging.getLogger()


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
    def __init__(self, *args, **kwargs):
        super().__init__(deepcopy(getattr(self, "__default_props__", {})))
        super().update(*args, **kwargs)

    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError(key)  # pylint: disable=raise-missing-from

    def __setattr__(self, key, value):
        self[key] = value

    def __delattr__(self, name):
        del self[name]

    @classmethod
    def new_from_file(cls, path):
        data = {}
        file_path = Path(path).resolve()
        if file_path.is_file():
            try:
                data = json.loads(file_path.read_text())
            except Exception as e:
                logger.error("Error '%s' opening JSON file %s: %s", type(e).__name__, file_path, e)
                logger.warning("Ignoring invalid JSON file (%s)", file_path)

        instance = _file_instances.get(file_path, cls())
        instance.update(data)
        _file_instances[file_path] = instance
        return instance

    def stringify(self, indent=4, sort_keys=True):
        return json.dumps(self, indent=indent, sort_keys=sort_keys)

    def save(self, *args, **kwargs) -> bool:
        self.update(*args, **kwargs)
        file_path = next((f for f, inst in _file_instances.items() if inst == self), None)

        return self.save_as(file_path)

    def save_as(self, path) -> bool:
        """Save self to file path"""
        file_path = Path(path).resolve()
        if file_path:
            try:
                # Ensure parent dir first
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.write_text(self.stringify())
                return True
            except Exception as e:
                logger.error("Error '%s' writing to JSON file %s: %s.", type(e).__name__, file_path, e)
        return False


def json_data_class(cls):
    # Moves the class props to __default_props__ (JsonData handles this)
    if not hasattr(cls, "__default_props__"):
        cls.__default_props__ = {}
    props = {k: v for k, v in vars(cls).items() if (not k.startswith("__") and not callable(getattr(cls, k)))}
    for prop, value in props.items():
        cls.__default_props__[prop] = value
        delattr(cls, prop)

    return cls
