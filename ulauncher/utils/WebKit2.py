import gi

# The version here just refers to the "build environment". Not the actual Webkit version
# 4.0 means it was built with GTK 3 and libsoup 2
# 4.1 means it was built with GTK 3 and libsoup 3 (HTTP/2)
# 5.0 means it was built with GTK 4 and libsoup 3 (incompatible w Ulauncher)
# https://blog.tingping.se/2021/06/07/http2-in-libsoup.html
# https://discourse.gnome.org/t/please-build-against-libsoup-3-by-default/10190
try:
    gi.require_version("WebKit2", "4.1")
except ValueError:
    gi.require_version("WebKit2", "4.0")
# pylint: disable=wrong-import-position,unused-import
from gi.repository import WebKit2  # type: ignore[attr-defined] # noqa: F401
