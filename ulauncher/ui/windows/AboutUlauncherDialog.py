# -*- Mode: Python; coding: utf-8; indent-tabs-mode: nil; tab-width: 4 -*-

from locale import gettext as _

import logging
logger = logging.getLogger('ulauncher')

from .AboutDialogBase import AboutDialogBase


class AboutUlauncherDialog(AboutDialogBase):
    __gtype_name__ = "AboutUlauncherDialog"

    def finish_initializing(self, builder):  # pylint: disable=E1002
        """Set up the about dialog"""
        super(AboutUlauncherDialog, self).finish_initializing(builder)

        # Code for other initialization actions should be added here.
