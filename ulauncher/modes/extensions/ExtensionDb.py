import json
import os.path

from ulauncher.config import PATHS
from ulauncher.modes.extensions import extension_finder
from ulauncher.utils.json_conf import JsonConf


class ExtensionRecord(JsonConf):
    id = ""
    url = ""
    updated_at = ""
    last_commit = ""
    last_commit_time = ""
    is_enabled = True

    @classmethod
    def create(cls, id, **kwargs):
        kwargs["id"] = id
        ext_path = extension_finder.locate(id)
        # TODO @nazarewk: ext_path can be None in the run_all() test  #noqa: TD003
        if ext_path is not None:
            record_file = os.path.join(ext_path, ".extension-record.json")
            if os.path.isfile(record_file):
                with open(record_file) as fp:
                    kwargs = {**json.load(fp), **kwargs}
        return cls(**kwargs)


class ExtensionDb(JsonConf):
    # Ensure all values are ExtensionRecords
    def __setitem__(self, key, value):
        if not isinstance(value, ExtensionRecord):
            value = ExtensionRecord.create(**value)
        super().__setitem__(key, value)

    def get_record(self, ext_id):
        if ext_id not in self:
            self[ext_id] = ExtensionRecord.create(ext_id)
            self.save()
        return self[ext_id]

    @classmethod
    def load(cls):
        return super().load(f"{PATHS.CONFIG}/extensions.json")
