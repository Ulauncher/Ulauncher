from __future__ import annotations

import os

# GDK Pixbuf uses https://gnome.pages.gitlab.gnome.org/glycin/ to parse images
# safely inside of a bwrap sandbox. When the whole test runs inside of a
# sandboxed environment, that fails because using bwrap itself needs access to
# create user and network namespaces. But it's redundant anyway
if os.environ.get("NONO_CAP_FILE"):
    from gi.repository import GLib

    GLib.set_prgname("gdk-pixbuf-thumbnailer")
