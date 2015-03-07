import os
import pickle
from distutils.dir_util import mkpath


class Db(object):

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
            pickle.dump(self._records, out, pickle.HIGHEST_PROTOCOL)
            out.close()

        return self

    def remove(self, desktop_file):
        """
        :param str desktop_file:
        :return bool: True if record was removed
        """
        try:
            del self._records[desktop_file]
            return True
        except KeyError:
            return False

    def get_records(self):
        return self._records
