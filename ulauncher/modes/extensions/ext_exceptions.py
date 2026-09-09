from __future__ import annotations


class ExtensionError(Exception):
    """Base class for all extension-related errors that can be caught together."""


class ManifestError(ExtensionError):
    """Raised when extension manifest is invalid or missing required fields."""


class CompatibilityError(ExtensionError):
    """Raised when extension is incompatible with current Ulauncher API version."""


class DependencyError(ExtensionError):
    """Raised when extension Python dependencies cannot be installed."""
