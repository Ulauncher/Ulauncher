import os
import pickle
from typing import Dict, Any

from distutils.dir_util import mkpath

Records = Dict[str, Any]


class KeyValueDb:
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
        self._records = {}

    def open(self) -> 'KeyValueDb':
        """Create a new data base or open existing one"""
        if os.path.exists(self._name):
            if not os.path.isfile(self._name):
                raise IOError("%s exists and is not a file" % self._name)

            with open(self._name, 'rb') as _in:  # binary mode
                self._records = pickle.load(_in)
        else:
            # make sure path exists
            mkpath(os.path.dirname(self._name))
            self.commit()

        return self

    def commit(self) -> 'KeyValueDb':
        """Write the database to a file"""
        with open(self._name, 'wb') as out:
            pickle.dump(self._records, out, pickle.HIGHEST_PROTOCOL)
            out.close()

        return self

    def remove(self, key: str) -> bool:
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

    def get_records(self) -> Records:
        return self._records

    def put(self, key: str, value: Any) -> None:
        self._records[key] = value

    def find(self, key: str, default: Any = None) -> Dict[Any, Any]:
        return self._records.get(key, default)
