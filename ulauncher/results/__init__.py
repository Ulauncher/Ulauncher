# -*- Mode: Python; coding: utf-8; indent-tabs-mode: nil; tab-width: 4 -*-

import logging
import ulauncher.backend.apps as apps
from ulauncher.backend.apps.desktop_reader import read_desktop_file
from . import ui
from . AppResultItem import AppResultItem
from gi.repository import Gtk


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
        r['icon'] = app.get_icon()

    return results
