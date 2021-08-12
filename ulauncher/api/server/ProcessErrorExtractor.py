import re

from ulauncher.api.shared.errors import UlauncherAPIError


class ProcessErrorExtractor:
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
            raise UlauncherAPIError('Could not extract errored module name from process output')

        return match.group(1)
