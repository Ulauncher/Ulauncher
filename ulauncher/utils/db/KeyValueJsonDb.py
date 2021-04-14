import os
import json
import logging
from distutils.dir_util import mkpath

from ulauncher.utils.db.KeyValueDb import KeyValueDb, Key, Value


class KeyValueJsonDb(KeyValueDb[Key, Value]):
    """
    Key-value JSON database
    Use open() method to load DB from a file and commit() to save it
    """

    def open(self) -> 'KeyValueJsonDb':
        """Create a new data base or open existing one"""
        if os.path.exists(self._name):
            if not os.path.isfile(self._name):
                raise IOError("%s exists and is not a file" % self._name)

            try:
                with open(self._name, 'r') as _in:
                    self.set_records(json.load(_in))
            except json.JSONDecodeError:
                # file corrupted, reset it.
                self.commit()
        else:
            # make sure path exists
            mkpath(os.path.dirname(self._name))
            self.commit()

        return self

    def commit(self) -> 'KeyValueJsonDb':
        """Write the database to a file"""
        try:
            with open(self._name, 'w') as out:
                json.dump(self._records, out, indent=4)
                out.close()
        except IOError as e:
            logging.error(e)

        return self
