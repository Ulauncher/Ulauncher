import os
import json
from .KeyValueDb import KeyValueDb
from distutils.dir_util import mkpath


class KeyValueJsonDb(KeyValueDb):
    """
    Key-value JSON database
    Use open() method to load DB from a file and commit() to save it
    """

    def open(self):
        """Create a new data base or open existing one"""
        if os.path.exists(self._name):
            if not os.path.isfile(self._name):
                raise IOError("%s exists and is not a file" % self._name)

            with open(self._name, 'r') as _in:
                self._records = json.load(_in)
        else:
            # make sure path exists
            mkpath(os.path.dirname(self._name))
            self.commit()

        return self

    def commit(self):
        """Write the database to a file"""
        with open(self._name, 'w') as out:
            json.dump(self._records, out, indent=4)
            out.close()

        return self
