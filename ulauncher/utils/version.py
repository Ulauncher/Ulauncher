# Ulauncher API version compatibility checking, featuring a subset of the "semver" standard, without the patch version.
# For backward compatibility with Ulauncher 5, the contraints are fully valid semver contraints.
# Hypen-ranges are supported, as well as the "x" wildcard syntax (x must be lowercase)
# Tilde and Caret are permitted, but ignored. Unlike semver the contraint "2.0" matches version 2.0 or newer
# There is no support for "*", "||", comparison operators like ">=", "!=", or the pre-release annotation


def get_version(version_string):
    sanitized = version_string.translate(str.maketrans({"^": "", "~": "", "x": ""}))
    major, minor, *_ = sanitized.split(".") + [None]
    return (int(major), int(minor) if minor else None)


def unpack_range(range_string):
    if " - " in range_string:
        [min_version, max_version] = map(get_version, range_string.split(" - "))
    else:
        min_version = get_version(range_string)
        max_version = get_version(str(min_version[0]))
    return min_version, max_version


def valid_range(range):
    try:
        (min_version, max_version) = unpack_range(range)
    except (ValueError, TypeError):
        return False
    if min_version[1] is None or max_version[1] is None:
        return min_version[0] <= max_version[0]
    return min_version <= max_version


def satisfies(version_string, expected_range):
    if not valid_range(expected_range):
        return False
    version = get_version(version_string)
    (min_version, max_version) = unpack_range(expected_range)
    if min_version[1] is None:
        min_version = (min_version[0], 0)
    if max_version[1] is None:
        max_version = (max_version[0], 99999999999999)
    return min_version <= version <= max_version
