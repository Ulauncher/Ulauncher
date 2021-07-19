from enum import Enum


class ErrorName(Enum):
    InvalidGithubUrl = 'InvalidGithubUrl'
    IncompatibleVersion = 'IncompatibleVersion'
    VersionsJsonNotFound = 'VersionsJsonNotFound'
    InvalidVersionsJson = 'InvalidVersionsJson'
    GithubApiError = 'GithubApiError'
    ExtensionAlreadyAdded = 'ExtensionAlreadyAdded'
    UnexpectedError = 'UnexpectedError'
    UnhandledError = 'UnhandledError'
    InvalidManifestJson = 'InvalidManifestJson'
    ExtensionCompatibilityError = 'ExtensionCompatibilityError'


class UlauncherAPIError(Exception):
    error_name = None  # type: str

    def __init__(self, message: str, error_name: ErrorName = ErrorName.UnexpectedError):
        super().__init__(message)
        self.error_name = error_name.value
