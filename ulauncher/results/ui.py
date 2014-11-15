import os
from gi.repository import Gtk
from ulauncher_lib.ulauncherconfig import get_data_file

ICON_SIZE = 40


def two_row_items(ui_file):
    """
    :param str ui_file: name of *.ui file for result item

    (Returns decorator function)
    func should return a list of dictionaries
    Each item is a dictionary with properties: icon_path, name, description
    Only  (str) `name` is mandatory
    Returns a list items as Gtk widgets
    """
    def items_decorator(func):
        def wrapper(*args, **kw):
            for i, item in enumerate(func(*args, **kw)):
                builder = create_item(ui_file)
                item_frame = builder.get_object('item-frame')
                item_frame.set_builder(builder)

                item_frame.set_icon(item['icon'])
                item_frame.set_name(item['name'])
                item_frame.set_description(item['description'])
                item_frame.set_shortcut(i + 1)
                item_frame.set_metadata(item)

                yield item_frame

        return wrapper
    return items_decorator


def create_item(builder_file_name):
    glade_filename = get_data_file('ui', '%s.ui' % (builder_file_name,))
    if not os.path.exists(glade_filename):
        glade_filename = None

    builder = Gtk.Builder()
    builder.set_translation_domain('ulauncher')
    builder.add_from_file(glade_filename)

    return builder
