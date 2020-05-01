import os
import pickle
from typing import Dict, TypeVar, Generic, Optional

Key = TypeVar('Key')
Value = TypeVar('Value')
Records = Dict[Key, Value]


class KeyValueDb(Generic[Key, Value]):
    """
    Key-value in-memory database
    Use open() method to load DB from a file and commit() to save it
    """

    _name = None  # type: str
    _records = None  # type: Records

    def __init__(self, basename: str):
        """
        :param str basename: path to db file
        """
        self._name = basename
        self.set_records({})

    def open(self) -> 'KeyValueDb':
        """Create a new data base or open existing one"""
        if os.path.exists(self._name):
            if not os.path.isfile(self._name):
                raise IOError("%s exists and is not a file" % self._name)

            if os.path.getsize(self._name) == 0:
                # ignore empty files
                return self

            with open(self._name, 'rb') as _in:  # binary mode
                self.set_records(pickle.load(_in))
        else:
            # make sure path exists
            os.makedirs(os.path.dirname(self._name), exist_ok=True)
            self.commit()

        return self

    def commit(self) -> 'KeyValueDb':
        """Write the database to a file"""
        with open(self._name, 'wb') as out:
            pickle_protocol = 2  # use 2 for BC with Ulauncher 4
            pickle.dump(self._records, out, pickle_protocol)
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
