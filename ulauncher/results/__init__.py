# -*- Mode: Python; coding: utf-8; indent-tabs-mode: nil; tab-width: 4 -*-

import logging
from ulauncher.backend.apps import find, get_plugins
from . import ui


logger = logging.getLogger(__name__)


@ui.two_row_items(ui_file='app_result_item')
def find_apps(text):
    result = find(text, min_score=68, limit=9)
    if len(result) > 0:
        return result

    '''If there is no result - we show plugins '''
    if '' != text:
        return get_plugins({"show_no_result": True})

    return []