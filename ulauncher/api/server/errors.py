from enum import Enum


class ErrorName(Enum):
    InvalidGithubUrl = 'InvalidGithubUrl'
    IncompatibleVersion = 'IncompatibleVersion'
    VersionsJsonNotFound = 'VersionsJsonNotFound'
    InvalidVersionsJson = 'InvalidVersionsJson'
    GithubApiError = 'GithubApiError'
    ExtensionAlreadyAdded = 'ExtensionAlreadyAdded'
    UnexpectedError = 'UnexpectedError'
    InvalidManifestJson = 'InvalidManifestJson'
    ExtensionCompatibilityError = 'ExtensionCompatibilityError'


class UlauncherServerError(Exception):
    error_name = None  # type: str

    def __init__(self, message: str, error_name: ErrorName):
        super(UlauncherServerError, self).__init__(message)
        self.error_name = error_name.value
