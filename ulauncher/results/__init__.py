# -*- Mode: Python; coding: utf-8; indent-tabs-mode: nil; tab-width: 4 -*-

import logging
from ulauncher.backend.apps import find
from . import ui


logger = logging.getLogger(__name__)


@ui.two_row_items(ui_file='app_result_item')
def find_apps(text):
    return find(text, min_score=68, limit=9)
