import os
import json
from gi.repository import Gtk
from ulauncher.config import get_data_file
from ulauncher.utils.lcs import lcs
from ulauncher.utils.Settings import Settings
from ulauncher.utils.lru_cache import lru_cache


def create_item(result_item, index, query):
    glade_filename = get_data_file('ui', '%s.ui' % result_item.UI_FILE)
    if not os.path.exists(glade_filename):
        glade_filename = None

    builder = Gtk.Builder()
    builder.set_translation_domain('ulauncher')
    builder.add_from_file(glade_filename)

    item_frame = builder.get_object('item-frame')
    item_frame.initialize(builder, result_item, index, query)

    return item_frame


def create_item_widgets(results, query):
    for i, result_item in enumerate(results):
        yield create_item(result_item, i, query)


def get_theme_name():
    return Settings.get_instance().get_property('theme-name')


@lru_cache()
def _read_theme(name):
    """Returns dict from data/ui/css/themes/<name>/theme.json"""
    filename = get_data_file('styles', 'themes', name, 'theme.json')
    with open(filename, 'r') as f:
        return json.load(f)


def get_theme_prop(name):
    return _read_theme(get_theme_name())[name]


@lru_cache(maxsize=150)
def highlight_text(query, text, open_tag='<span foreground="white">', close_tag='</span>'):
    """
    Highlights words from query in a given text string
    Retuns string with Pango markup
    """
    positions = set()  # indexes of symbols in 'text' that need to be highlighted
    parts = []  # holds tupples (<index of sub-text in 'text'>, <sub-query>, <sub-text>)
    # split query by whitespaces, because we don't want to take into account order of separate words in a query
    map(parts.append, [(0, q.strip(), text.lower()) for q in query.lower().split(' ')])
    while parts:
        # iteratively create and walk through all pairs of sub-query and sub-text
        # and add sub-text indexes of longest common string to 'positions' set
        offset, sub_query, sub_text = parts.pop()
        lc_str = lcs(sub_query, sub_text)
        if lc_str:
            lcs_idx_q = sub_query.index(lc_str)
            lcs_idx_t = sub_text.index(lc_str)
            # add indexes of LCS to position
            map(positions.add, range(offset + lcs_idx_t, offset + lcs_idx_t + len(lc_str)))

            left_q = sub_query[:lcs_idx_q]
            left_t = sub_text[:lcs_idx_t]
            if left_q and left_t:
                # add the remaining part of query and string before LCS
                parts.append((offset, left_q, left_t))

            right_q = sub_query[lcs_idx_q + len(lc_str):]
            right_t = sub_text[lcs_idx_t + len(lc_str):]
            if right_q and right_t:
                # add the remaining part of query and string after LCS
                parts.append((offset + lcs_idx_t + len(lc_str), right_q, right_t))

    # use positions to highlight text with tags
    hl_started = False
    hlted = []
    for i in range(len(text)):
        if i in positions and not hl_started:
            hl_started = True
            hlted.append(open_tag)
        elif i not in positions and hl_started:
            hl_started = False
            hlted.append(close_tag)

        hlted.append(text[i])

    if hl_started:
        # don't forget to close tag if it is opened
        hlted.append(close_tag)

    # replace & characters with &amp;
    return ''.join(hlted).replace('&', '&amp;')
