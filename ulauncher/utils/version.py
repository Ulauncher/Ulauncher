from __future__ import annotations

import sys
from typing import Optional, Tuple

# Ulauncher API version compatibility checking, featuring a subset of the "semver" standard, without the patch version.
# For backward compatibility with Ulauncher 5, the constraints are fully valid semver constraints.
# Hyphen-ranges are supported, as well as the "x" wildcard syntax (x must be lowercase)
# Tilde and Caret are permitted, but ignored. Unlike semver the constraint "2.0" matches version 2.0 or newer
# There is no support for "*", "||", comparison operators like ">=", "!=", or the pre-release annotation

# versions like "1" and "1.x" will be parsed into (1, None)
VersionRepr = Tuple[int, Optional[int]]


def _parse_version(version_string: str) -> VersionRepr:
    t_table = str.maketrans({"^": "", "~": "", "x": ""})
    sanitized = version_string.translate(t_table)
    parts = [int(x) if x else None for x in sanitized.split(".")] + [None]
    return (parts[0] or 0, parts[1])


def _unpack_range(range_str: str) -> tuple[VersionRepr, VersionRepr]:
    if " - " in range_str:
        [min_version, max_version] = map(_parse_version, range_str.split(" - "))
    else:
        min_version = _parse_version(range_str)
        max_version = _parse_version(str(min_version[0]))
    return min_version, max_version


def _valid_range(range_str: str) -> bool:
    try:
        (min_version, max_version) = _unpack_range(range_str)
    except (ValueError, TypeError):
        return False
    if min_version[1] is None or max_version[1] is None:
        return min_version[0] <= max_version[0]
    return min_version <= max_version


def get_version(version_string: str) -> tuple[int, int]:
    """Parse a version string into a (major, minor) tuple."""
    major, minor = _parse_version(version_string)
    return (major, minor or 0)


def satisfies(version_string: str, expected_range: str) -> bool:
    if not _valid_range(expected_range):
        return False
    version = get_version(version_string)
    min_version, max_version = _unpack_range(expected_range)
    if min_version[1] is None:
        min_version = (min_version[0], 0)
    if max_version[1] is None:
        max_version = (max_version[0], sys.maxsize)
    return min_version <= version <= max_version
