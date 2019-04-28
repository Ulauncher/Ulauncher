import os
import pickle
from distutils.dir_util import mkpath


class KeyValueDb(object):
    """
    Key-value in-memory database
    Use open() method to load DB from a file and commit() to save it
    """

    _name = None
    _records = None

    def __init__(self, basename):
        """
        :param str basename: path to db file
        """
        self._name = basename
        self._records = {}

    def open(self):
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

    def commit(self):
        """Write the database to a file"""
        with open(self._name, 'wb') as out:
            # use protocol 2 for compatibility with future versions
            pickle.dump(self._records, out, 2)
            out.close()

        return self

    def remove(self, key):
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

    def get_records(self):
        return self._records

    def put(self, key, value):
        self._records[key] = value

    def find(self, key, default=None):
        return self._records.get(key, default)
