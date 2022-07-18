from ulauncher.config import PATHS
from ulauncher.utils.json_data import JsonData, json_data_class


@json_data_class
class ExtensionRecord(JsonData):
    id = ""
    url = ""
    updated_at = ""
    last_commit = ""
    last_commit_time = ""


class ExtensionDb(JsonData):
    # Ensure all values are ExtensionRecords
    def __setitem__(self, key, value):
        super().__setitem__(key, ExtensionRecord(value))

    @classmethod
    def load(cls):
        return cls.new_from_file(f"{PATHS.CONFIG}/extensions.json")
