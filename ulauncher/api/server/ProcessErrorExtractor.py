import re
import io
from itertools import takewhile

from ulauncher.api.shared.errors import UlauncherAPIError


class ProcessErrorExtractor:

    @classmethod
    def extract_from_file_object(cls, file: io.BytesIO) -> 'ProcessErrorExtractor':
        error = b''
        for line in takewhile(bool, iter(file.readline, b'')):
            if line:
                error = line

        return cls(error.decode('utf-8') if isinstance(error, bytes) else error)

    def __init__(self, error: str):
        """
        expecting an error like this:
            ModuleNotFoundError: No module named 'mymodule'
        """
        self.error = error

    def is_import_error(self) -> bool:
        return 'ModuleNotFoundError' in self.error

    def get_missing_package_name(self) -> str:
        """
        Returns a name of a module that extension failed to import
        """
        match = re.match(r"^.*'(\w+)'$", self.error)
        if not match:
            raise UlauncherAPIError('Could not exctract errored module name from process output')

        return match.group(1)
