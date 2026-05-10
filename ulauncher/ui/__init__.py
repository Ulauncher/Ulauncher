import gi

# pin gi versions for all use inside the ui directory tree
gi.require_versions(
    {
        "Gdk": "3.0",
        "GdkPixbuf": "2.0",
        "GdkX11": "3.0",
        "Gtk": "3.0",
        "Pango": "1.0",
    }
)
