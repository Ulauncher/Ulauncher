import gi
try:
    # 4.1 is the only supported version in Arch
    # Trying to load 4.0 if you have both 4.1 and 5.0 give you 5.0 (unsupported libadwaita version)
    # So we must try with 4.1 first
    gi.require_version("WebKit2", "4.1")
except ValueError:
    # 4.0 is the only version that exists for most older distro version, like Ubuntu before 22.04
    gi.require_version("WebKit2", "4.0")
# pylint: disable=wrong-import-position,unused-import
from gi.repository import WebKit2  # noqa: F401
