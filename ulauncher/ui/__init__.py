import os
import json
from gi.repository import Gtk
from ulauncher.config import get_data_file
from ulauncher.utils.fuzzy_search import get_matching_indexes
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


def highlight_text(query, text, open_tag='<span foreground="white">', close_tag='</span>'):
    """
    Highlights words from query in a given text string
    Retuns string with Pango markup
    """
    positions = get_matching_indexes(query, text)

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
