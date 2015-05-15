from gi.repository import Gtk
import logging
logger = logging.getLogger(__name__)

from . import get_builder


class PreferencesDialogBase(Gtk.Dialog):
    __gtype_name__ = "PreferencesDialog"

    def __new__(cls):
        """Special static method that's automatically called by Python when
        constructing a new instance of this class.

        Returns a fully instantiated PreferencesDialog object.
        """
        builder = get_builder('PreferencesUlauncherDialog')
        new_object = builder.get_object("preferences_ulauncher_dialog")
        new_object.finish_initializing(builder)
        return new_object

    def finish_initializing(self, builder):
        """Called while initializing this instance in __new__

        finish_initalizing should be called after parsing the ui definition
        and creating a PreferencesDialog object with it in order to
        finish initializing the start of the new PerferencesUlauncherDialog
        instance.

        Put your initialization code in here and leave __init__ undefined.
        """

        # Get a reference to the builder and set up the signals.
        self.builder = builder
        self.ui = builder.get_ui(self, True)
