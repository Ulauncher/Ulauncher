# -*- Mode: Python; coding: utf-8; indent-tabs-mode: nil; tab-width: 4 -*-

import logging
import ulauncher.backend.apps as apps
from ulauncher.backend.apps.desktop_reader import read_desktop_file
from . import ui
from . AppResultItem import AppResultItem
from gi.repository import Gtk, Gio


icon_theme = Gtk.IconTheme()
logger = logging.getLogger(__name__)


def find_results_for_input(text, callback):
    """
    :param str text:
    :param fun callback: Takes list of GtkWidgets as a first argument
    """
    callback(find_apps(text))


@ui.two_row_items(ui_file='app_result_item')
def find_apps(text):
    results = apps.find(text, min_score=68, limit=9)
    for r in results:
        app = read_desktop_file(r['desktop_file'])

        icon = app.get_icon()
        if isinstance(icon, Gio.ThemedIcon):
            try:
                icon_name = icon.get_names()[0]
                r['icon'] = icon_theme.load_icon(icon_name, AppResultItem.ICON_SIZE, Gtk.IconLookupFlags.FORCE_SIZE)
            except Exception as e:
                logger.debug('Could not load icon for %s -> %s', r['desktop_file'], e)
        elif isinstance(icon, Gio.FileIcon):
            r['icon'] = icon.get_file().get_path()

    return results
