# Eventually we should switch to define these in pyproject.toml and import with
# tomllib (py3.11) w fallback to tomli: https://github.com/Ulauncher/Ulauncher/blob/1cdaeb4d28eacfddda887690072d4e3ecd02baff/ulauncher/__init__.py#L4-L15
# importlib.metadata (Py3.8) also works (but just for version): importlib.metadata.version("ulauncher")


version = "6.0.0-b5"
gi_versions = {
    "Gtk": "3.0",
    "Gdk": "3.0",
    "GdkX11": "3.0",
    "GdkPixbuf": "2.0",
    "Pango": "1.0",
}

# this namespace module is the only way we can pin gi versions globally,
# but we also use it when we build, then we don't want to require gi
try:
    import gi

    gi.require_versions(gi_versions)
except ModuleNotFoundError:
    pass
