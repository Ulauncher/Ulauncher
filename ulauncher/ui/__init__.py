import os
from gi.repository import Gtk
from ulauncher.config import get_data_file


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
