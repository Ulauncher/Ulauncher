from ulauncher.utils.fuzzy_search import get_matching_blocks
from gi.repository import Gtk

# def highlight_text(query: str, text: str) -> list:
#     """
#     Highlights words from query in a given text string
#     :returns: list of Gtk labels
#     """
#     labels = []

#     start_index = 0

#     for index, chars in get_matching_blocks(query, text)[0]:
#         chars_len = len(chars)

#         if index > start_index:
#             labels.append(Gtk.Label(max_width_chars=1, xalign=0, label=text[start_index:index]))

#         highlight_label = Gtk.Label(max_width_chars=1, xalign=0, label=text[index:index + chars_len])
#         highlight_label.get_style_context().add_class("item-highlight")
#         labels.append(highlight_label)

#         start_index = index + chars_len

#     if start_index < len(text):
#         labels.append(Gtk.Label(label=text[start_index:]))

#     return labels

def highlight_text(query: str, text: str, max_length = 50) -> list:
    """
    Highlights words from query in a given text string. Ellipsizes the text if it is too long.
    :returns: list of Gtk labels
    """
    labels = []
    start_index = 0
    ellipsis = '...'

    for index, chars in get_matching_blocks(query, text)[0]:
        chars_len = len(chars)

        if index > start_index:
            if index - start_index <= max_length:
                labels.append(Gtk.Label(max_width_chars=1, xalign=0, label=text[start_index:index]))
            else:
                labels.append(Gtk.Label(max_width_chars=1, xalign=0, label=text[start_index:start_index + 50] + ellipsis))

        highlight_label = Gtk.Label(max_width_chars=1, xalign=0, label=text[index:index + chars_len])
        highlight_label.get_style_context().add_class("item-highlight")
        labels.append(highlight_label)

        start_index = index + chars_len

    if start_index < len(text):
        if len(text) - start_index <= max_length:
            labels.append(Gtk.Label(label=text[start_index:]))
        else:
            labels.append(Gtk.Label(label=text[start_index:start_index + 50] + ellipsis))

    return labels
