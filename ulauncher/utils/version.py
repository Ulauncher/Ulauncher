from __future__ import annotations

from typing import Optional, Tuple

# Ulauncher API version compatibility checking, featuring a subset of the "semver" standard, without the patch version.
# For backward compatibility with Ulauncher 5, the constraints are fully valid semver constraints.
# Hyphen-ranges are supported, as well as the "x" wildcard syntax (x must be lowercase)
# Tilde and Caret are permitted, but ignored. Unlike semver the constraint "2.0" matches version 2.0 or newer
# There is no support for "*", "||", comparison operators like ">=", "!=", or the pre-release annotation

Version = Tuple[int, Optional[int]]


def get_version(version_string: str) -> Version:
    t_table = str.maketrans({"^": "", "~": "", "x": ""})
    sanitized = version_string.translate(t_table)
    parts = [int(x) if x else None for x in sanitized.split(".")] + [None]
    return (parts[0] or 0, parts[1])


def unpack_range(range_string: str) -> tuple[Version, Version]:
    if " - " in range_string:
        [min_version, max_version] = map(get_version, range_string.split(" - "))
    else:
        min_version = get_version(range_string)
        max_version = get_version(str(min_version[0]))
    return min_version, max_version


def valid_range(rng: str) -> bool:
    try:
        (min_version, max_version) = unpack_range(rng)
    except (ValueError, TypeError):
        return False
    if min_version[1] is None or max_version[1] is None:
        return min_version[0] <= max_version[0]
    return min_version <= max_version


def satisfies(version_string: str, expected_range: str) -> bool:
    if not valid_range(expected_range):
        return False
    version = get_version(version_string)
    (min_version, max_version) = unpack_range(expected_range)
    if min_version[1] is None:
        min_version = (min_version[0], 0)
    if max_version[1] is None:
        max_version = (max_version[0], 99999999999999)
    return min_version <= version <= max_version
