from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, TypeVar, cast

from ulauncher.utils.basedataclass import BaseDataClass


def _filter_recursive(data, blacklist):
    if isinstance(data, dict):
        return {k: _filter_recursive(v, blacklist) for k, v in data.items() if v not in blacklist}
    if isinstance(data, list):
        return [_filter_recursive(v, blacklist) for v in data]
    return data


# See https://stackoverflow.com/a/63237226/633921 for why JsonConf is quoted
_file_instances: dict[tuple[Path, type], JsonConf] = {}
logger = logging.getLogger()
T = TypeVar("T", bound="JsonConf")


def stringify(data, indent=None, sort_keys=True, value_blacklist: list[Any] | None = None) -> str:
    # When serializing to JSON, filter out common empty default values like None, empty list or dict
    # These are default values when initializing the objects, but they are not actual data
    if value_blacklist is None:
        value_blacklist = [[], {}, None, ""]
    filtered_data = _filter_recursive(data, value_blacklist)
    return json.dumps(filtered_data, indent=indent, sort_keys=sort_keys)


def save_as(data, path, indent=2, sort_keys=True, value_blacklist: list[Any] | None = None) -> bool:
    """Save self to file path"""
    # When serializing to JSON, filter out common empty default values like None, empty list or dict
    # These are default values when initializing the objects, but they are not actual data
    file_path = Path(path).resolve()
    if file_path:
        try:
            # Ensure parent dir first
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(stringify(data, indent=indent, sort_keys=sort_keys, value_blacklist=value_blacklist))
        except Exception:
            logger.exception('Could not write to JSON file "%s"', file_path)
        else:
            return True
    return False


class JsonConf(BaseDataClass):
    """
    JsonConf

    This is an helper class to handle json config files
    It has two convenient methods for loading and saving the data, which also depuplicate class instances,
    So that if you create two instances for the same file it will actually reuse the first instance
    (to avoid overwriting state changes)

    File paths are stored in an external reference object, which is not part of the data.
    """

    @classmethod
    def load(cls: type[T], path) -> T:
        data = {}
        file_path = Path(path).resolve()
        key = (file_path, cls)
        if key not in _file_instances and file_path.is_file():
            try:
                data = json.loads(file_path.read_text())
            except Exception:
                logger.exception('Error opening JSON file "%s"', file_path)
                logger.warning('Ignoring invalid JSON file "%s"', file_path)

        instance = _file_instances.get(key, cls())
        instance.update(data)
        _file_instances[key] = instance
        return cast(T, instance)

    def save(self, sort_keys=True, indent=2, value_blacklist: list[Any] | None = None) -> bool:
        file_path = next((key[0] for key, inst in _file_instances.items() if inst == self), None)

        return save_as(self, file_path, sort_keys, indent, value_blacklist)
