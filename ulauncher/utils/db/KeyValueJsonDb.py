import json
from pathlib import Path
from typing import Dict, TypeVar, Generic, Optional
from logging import getLogger

Key = TypeVar('Key')
Value = TypeVar('Value')
Records = Dict[Key, Value]

logger = getLogger(__name__)


class KeyValueJsonDb(Generic[Key, Value]):
    """
    Key-value in-memory database
    Use open() method to load JSON from a file and commit() to save it
    """

    _path = None  # type: Path
    _records = None  # type: Records

    def __init__(self, path: str):
        """
        :param str basename: path to db file
        """
        self._path = Path(path)
        self.set_records({})

    def open(self) -> 'KeyValueJsonDb':
        """Create a new data base or open existing one"""
        # Ensure parent dir
        self._path.parent.mkdir(parents=True, exist_ok=True)

        if self._path.exists():
            try:
                self.set_records(json.loads(self._path.read_text()))
            except Exception as e:
                logger.error("Error '%s' opening JSON file %s: %s", type(e).__name__, self._path, e)
                logger.warning("Resetting invalid JSON file (%s)", self._path)
                if not self.commit():
                    logger.warning("Failed to reset JSON file")

        return self

    def commit(self) -> bool:
        """Write the database to a file"""
        try:
            self._path.write_text(json.dumps(self._records, indent=4))
            return True
        except Exception as e:
            logger.error("Error '%s' writing to JSON file %s: %s.", type(e).__name__, self._path, e)
        return False

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
