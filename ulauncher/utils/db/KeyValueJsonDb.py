import os
import json

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
            os.makedirs(os.path.dirname(self._name), exist_ok=True)
            self.commit()

        return self

    def commit(self) -> 'KeyValueJsonDb':
        """Write the database to a file"""
        with open(self._name, 'w') as out:
            json.dump(self._records, out, indent=4)
            out.close()

        return self
