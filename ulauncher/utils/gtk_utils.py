from __future__ import annotations

from gi.repository import Gtk


def ui_snapshot(ui: Gtk.Widget) -> str:
    """Generate a tree-like structure of all UI elements and their properties."""

    lines: list[str] = []
    lines.append("=== UI Snapshot ===")
    lines.extend(_get_widget_snapshot_recursively(ui, 0, True))
    lines.append("===================")

    return "\n".join(lines)


def _get_widget_snapshot_recursively(widget: Gtk.Widget, depth: int, is_last: bool) -> list[str]:  # noqa: PLR0912
    """Recursively get a snapshot of the widget and its children."""

    lines: list[str] = []
    indent = "  " * depth
    text = ""
    widget_name = widget.get_name() or type(widget).__name__

    properties = []
    if not widget.get_visible():
        properties.append("hidden")

    if hasattr(widget, "get_text"):
        text = f"[{widget.get_text()}]"

    if hasattr(widget, "get_style_context"):
        style_context = widget.get_style_context()
        class_names = style_context.list_classes()
        if class_names:
            properties.append(f"classes=[{', '.join(class_names)}]")

    parent = widget.get_parent()
    if parent and isinstance(parent, Gtk.Box):
        expand, fill, padding, pack_type = parent.query_child_packing(widget)
        if expand:
            properties.append("expand")
        if fill:
            properties.append("fill")
        if padding > 0:
            properties.append(f"padding={padding}")
        properties.append(f"pack_type={pack_type.value_nick}")

    if hasattr(widget, "get_width_request"):
        width = widget.get_width_request()
        if width > 0:
            properties.append(f"width_request={width}")

    if hasattr(widget, "get_height_request"):
        height = widget.get_height_request()
        if height > 0:
            properties.append(f"height_request={height}")

    props_str = ", ".join(properties) if properties else ""
    children = (isinstance(widget, Gtk.Container) and widget.get_children()) or []
    branch_symbol = "└─" if is_last or children else "├─"
    lines.append(f"{indent}{branch_symbol} {widget_name}{text}: {props_str}")

    # Recursively get children snapshot
    for child in children:
        is_last_child = child == children[-1]
        lines.extend(_get_widget_snapshot_recursively(child, depth + 1, is_last_child))

    return lines
