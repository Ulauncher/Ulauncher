import sys
from pathlib import Path

if sys.version_info >= (3, 11):
    import tomllib  # tomllib only exists in python>=3.11
else:
    import tomli as tomllib


_project_root = Path(__file__).parent.parent

with Path(_project_root, "pyproject.toml").open("rb") as f:
    _pyproject = tomllib.load(f)
    version = _pyproject["project"]["version"]
    gi_versions = _pyproject.get("tool", {}).get("gobject", {}).get("pin_versions", {})

# this namespace module is the only way we can pin gi versions globally,
# but we also use it when we build, then we don't want to require gi
try:
    import gi

    gi.require_versions(gi_versions)
except ModuleNotFoundError:
    pass
