from ulauncher.config import PATHS
from ulauncher.utils.json_conf import JsonConf


class ExtensionRecord(JsonConf):
    id = ""
    url = ""
    updated_at = ""
    last_commit = ""
    last_commit_time = ""
    is_enabled = True


class ExtensionDb(JsonConf):
    # Ensure all values are ExtensionRecords
    def __setitem__(self, key, value):
        super().__setitem__(key, ExtensionRecord(value))

    @classmethod
    def load(cls):
        return super().load(f"{PATHS.CONFIG}/extensions.json")
