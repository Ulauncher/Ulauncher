import os
from gi.repository import Gtk
from ulauncher.config import get_data_file
from ulauncher.ext.ResultItem import ResultItem


def create_item(result_item, index, query):
    if isinstance(result_item, ResultItem):
        ui_file = 'result_item'  # default item UI
    else:
        raise TypeError('Invalid type "%s" for result item' % type(result_item))

    glade_filename = get_data_file('ui', '%s.ui' % ui_file)
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
