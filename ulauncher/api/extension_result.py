import logging
import json
import sys
from functools import lru_cache
from pathlib import Path
from ulauncher.api.shared.action.BaseAction import BaseAction
from .result import Result

logger = logging.getLogger()


@lru_cache(maxsize=1)
def get_icon_from_manifest(ext_dir):
    try:
        manifest = json.loads(Path(ext_dir, "manifest.json").read_text())
        return manifest.get("icon")
    except Exception as e:
        logger.exception("Couldn't load icon from manifest: %s", e)
        return None


class ExtensionResult(Result):
    """
    Should be used in extensions.

    Cannot be subclassed there because :func:`pickle.loads` won't work in Ulauncher app
    """

    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        ext_dir = Path(sys.argv[0]).parent
        if not self.icon:
            self.icon = get_icon_from_manifest(ext_dir)

        full_icon_path = self.icon and Path(ext_dir, self.icon)
        if self.icon and full_icon_path.is_file():
            self.icon = str(full_icon_path)  # else assume it's a standard icon name like "edit-paste"

        if self._on_enter and not isinstance(self._on_enter, BaseAction):
            raise Exception("Invalid on_enter argument. Expected BaseAction")

    def on_enter(self, query):
        return self._on_enter

    def on_alt_enter(self, query):
        return self._on_alt_enter
