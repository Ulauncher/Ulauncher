from enum import Enum


class ExtensionError(Enum):
    AlreadyAdded = 'AlreadyAdded'
    Incompatible = 'Incompatible'
    InvalidManifest = 'InvalidManifest'
    InvalidUrl = 'InvalidUrl'
    InvalidVersionDeclaration = 'InvalidVersionDeclaration'
    MissingVersionDeclaration = 'MissingVersionDeclaration'
    Network = 'Network'
    Other = 'Other'


class UlauncherAPIError(Exception):
    error_name = None  # type: str

    def __init__(self, message: str, error_name: ExtensionError = ExtensionError.Other):
        super().__init__(message)
        self.error_name = error_name.value
