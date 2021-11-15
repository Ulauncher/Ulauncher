import os
import json
from typing import Dict, TypeVar, Generic, Optional

Key = TypeVar('Key')
Value = TypeVar('Value')
Records = Dict[Key, Value]


class KeyValueJsonDb(Generic[Key, Value]):
    """
    Key-value in-memory database
    Use open() method to load JSON from a file and commit() to save it
    """

    _path = None  # type: str
    _records = None  # type: Records

    def __init__(self, path: str):
        """
        :param str basename: path to db file
        """
        self._path = path
        self.set_records({})

    def open(self) -> 'KeyValueJsonDb':
        """Create a new data base or open existing one"""
        if os.path.exists(self._path):
            if not os.path.isfile(self._path):
                raise IOError("%s exists and is not a file" % self._path)

            try:
                with open(self._path, 'r') as _in:
                    self.set_records(json.load(_in))
            except json.JSONDecodeError:
                # file corrupted, reset it.
                self.commit()
        else:
            # make sure path exists
            os.makedirs(os.path.dirname(self._path), exist_ok=True)
            self.commit()

        return self

    def commit(self) -> 'KeyValueJsonDb':
        """Write the database to a file"""
        with open(self._path, 'w') as out:
            json.dump(self._records, out, indent=4)
            out.close()

        return self

    def remove(self, key: Key) -> bool:
        """
        :param str key:
        :type: bool
        :return: True if record was removed
        """
        try:
            del self._records[key]
            return True
        except KeyError:
            return False

    def set_records(self, records: Records):
        self._records = records

    def get_records(self) -> Records:
        return self._records

    def put(self, key: Key, value: Value) -> None:
        self._records[key] = value

    def find(self, key: Key, default: Value = None) -> Optional[Value]:
        return self._records.get(key, default)
