# pylint: disable-all
import gi

# The package version refers to the "build environment". Not the actual Webkit version
# 4.0 means it was built with GTK 3 and libsoup 2
# 4.1 means it was built with GTK 3 and libsoup 3 (HTTP/2)
# 5.0 means it was built with GTK 4 and libsoup 3 (incompatible w Ulauncher, and was only supported for a short period)
# 6.0 means the same as 5.0, but the API has major changes, and the package name was renamed, dropping the "2"
# https://blog.tingping.se/2021/06/07/http2-in-libsoup.html
# https://discourse.gnome.org/t/please-build-against-libsoup-3-by-default/10190
# https://bugs.webkit.org/show_bug.cgi?id=245296
try:
    gi.require_version('WebKit2', '4.1')
except ValueError:
    gi.require_version('WebKit2', '4.0')
from gi.repository import WebKit2  # type: ignore[attr-defined] # noqa: F401
