import os
import json
import logging

from ulauncher.utils.db.KeyValueDb import KeyValueDb, Key, Value

logger = logging.getLogger(__name__)


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
                    records = json.load(_in)
            # a half-written file is not valid json, and a binary one is not even text
            except ValueError as e:
                logger.error("Cannot read %s, so it will be overwritten. %s: %s",
                             self._name, type(e).__name__, e)
                self.commit()
            else:
                if isinstance(records, dict):
                    self.set_records(records)
                else:
                    logger.error("%s holds %s instead of a dict, so it will be overwritten",
                                 self._name, type(records).__name__)
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
