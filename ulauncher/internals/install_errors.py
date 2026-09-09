from __future__ import annotations


class InstallError(Exception):
    """Raised when the remote repository being installed from fails (not network-related).

    Also the base class for all repo-install errors that can be caught together.
    """


class NetworkError(InstallError):
    """Raised when there's a network error accessing the repository."""


class UrlError(InstallError):
    """Raised when the repo URL/path cannot be parsed."""
