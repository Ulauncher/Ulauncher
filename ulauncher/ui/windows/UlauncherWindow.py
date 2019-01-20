# -*- Mode: Python; coding: utf-8; indent-tabs-mode: nil; tab-width: 4 -*-
import os
import time
import logging
import threading
import subprocess
import mimetypes


import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
gi.require_version('GLib', '2.0')
gi.require_version('Keybinder', '3.0')

from gi.repository import Gtk, Gdk, GLib, Keybinder

# these imports are needed for Gtk to find widget classes
from ulauncher.ui.ResultItemWidget import ResultItemWidget
from ulauncher.ui.SmallResultItemWidget import SmallResultItemWidget

from ulauncher.config import get_data_file, is_wayland_compatibility_on
from ulauncher.ui.ItemNavigation import ItemNavigation
from ulauncher.search.Search import Search
from ulauncher.search.apps.AppStatDb import AppStatDb
from ulauncher.api.server.ExtensionRunner import ExtensionRunner
from ulauncher.api.server.ExtensionServer import ExtensionServer
from ulauncher.api.server.ExtensionDownloader import ExtensionDownloader
from ulauncher.util.AppCacheDb import AppCacheDb
from ulauncher.util.Settings import Settings
from ulauncher.util.decorator.singleton import singleton
from ulauncher.util.display import get_current_screen_geometry
from ulauncher.util.string import force_unicode
from ulauncher.util.version_cmp import gtk_version_is_gte
from ulauncher.util.desktop.notification import show_notification
from ulauncher.util.Theme import Theme, load_available_themes
from ulauncher.search.apps.app_watcher import start as start_app_watcher
from ulauncher.search.Query import Query
from .Builder import Builder
from .WindowHelper import WindowHelper
from .PreferencesUlauncherDialog import PreferencesUlauncherDialog

logger = logging.getLogger(__name__)


class UlauncherWindow(Gtk.Window, WindowHelper):
    __gtype_name__ = "UlauncherWindow"

    _current_accel_name = None
    _results_render_time = 0

    @classmethod
    @singleton
    def get_instance(cls):
        return cls()

    def __new__(cls):
        """Special static method that's automatically called by Python when
        constructing a new instance of this class.

        Returns a fully instantiated BaseUlauncherWindow object.
        """
        builder = Builder.new_from_file('UlauncherWindow')
        new_object = builder.get_object("ulauncher_window")
        new_object.finish_initializing(builder)
        return new_object

    def finish_initializing(self, builder):
        """Called while initializing this instance in __new__

        finish_initializing should be called after parsing the UI definition
        and creating a UlauncherWindow object with it in order to finish
        initializing the start of the new UlauncherWindow instance.
        """
        # Get a reference to the builder and set up the signals.
        self.builder = builder
        self.ui = builder.get_ui(self, True)
        self.PreferencesDialog = None  # class
        self.preferences_dialog = None  # instance

        self.results_nav = None
        self.window = self.ui['ulauncher_window']
        self.input = self.ui['input']
        self.prefs_btn = self.ui['prefs_btn']
        self.result_box = self.ui["result_box"]

        self.result_box_parent = self.result_box.get_parent()

        self.input.connect('changed', self.on_input_changed)
        self.prefs_btn.connect('clicked', self.on_mnu_preferences_activate)

        self.set_keep_above(True)

        self.PreferencesDialog = PreferencesUlauncherDialog
        self.settings = Settings.get_instance()

        self.fix_window_width()
        self.position_window()
        self.init_theme()

        # this will trigger to show frequent apps if necessary
        self.show_results([])

        if not is_wayland_compatibility_on():
            # bind hotkey
            Keybinder.init()
            accel_name = self.settings.get_property('hotkey-show-app')
            # bind in the main thread
            GLib.idle_add(self.bind_show_app_hotkey, accel_name)

        start_app_watcher()
        ExtensionServer.get_instance().start()
        time.sleep(0.01)
        ExtensionRunner.get_instance().run_all()
        ExtensionDownloader.get_instance().download_missing()

    ######################################
    # GTK Signal Handlers
    ######################################

    def on_mnu_about_activate(self, widget, data=None):
        """Display the about page for ulauncher."""
        self.activate_preferences(page='about')

    def on_mnu_preferences_activate(self, widget, data=None):
        """Display the preferences window for ulauncher."""
        self.activate_preferences(page='preferences')

    def on_mnu_close_activate(self, widget, data=None):
        """Signal handler for closing the UlauncherWindow."""
        self.destroy()

    def on_destroy(self, widget, data=None):
        """Called when the UlauncherWindow is closed."""
        # Clean up code for saving application state should be added here.
        Gtk.main_quit()

    def on_preferences_dialog_destroyed(self, widget, data=None):
        '''only affects GUI

        logically there is no difference between the user closing,
        minimizing or ignoring the preferences dialog'''
        logger.debug('on_preferences_dialog_destroyed')
        # to determine whether to create or present preferences_dialog
        self.preferences_dialog = None

    def on_focus_out_event(self, widget, event):
        # apparently Gtk doesn't provide a mechanism to tell if window is in focus
        # this is a simple workaround to avoid hiding window
        # when user hits Alt+key combination or changes input source, etc.
        self.is_focused = False
        t = threading.Timer(0.07, lambda: self.is_focused or self.hide())
        t.start()

    def on_focus_in_event(self, *args):
        self.is_focused = True

    def on_input_changed(self, entry):
        """
        Triggered by user input
        """
        Search.get_instance().on_query_change(self._get_user_query())

    def on_input_key_press_event(self, widget, event):
        keyval = event.get_keyval()
        keyname = Gdk.keyval_name(keyval[1])
        alt = event.state & Gdk.ModifierType.MOD1_MASK
        Search.get_instance().on_key_press_event(widget, event, self._get_user_query())

        if self.results_nav:
            if keyname == 'Up':
                self.results_nav.go_up()
            elif keyname == 'Down':
                self.results_nav.go_down()
            elif alt and keyname in ('Return', 'KP_Enter'):
                self.enter_result_item(alt=True)
            elif keyname in ('Return', 'KP_Enter'):
                self.enter_result_item()
            elif alt and keyname.isdigit() and 0 < int(keyname) < 10:
                # on Alt+<num>
                try:
                    self.enter_result_item(int(keyname) - 1)
                except IndexError:
                    # selected non-existing result item
                    pass
            elif alt and len(keyname) == 1 and 97 <= ord(keyname) <= 122:
                # on Alt+<char>
                try:
                    self.enter_result_item(ord(keyname) - 97 + 9)
                except IndexError:
                    # selected non-existing result item
                    pass

        if keyname == 'Escape':
            self.hide()

    ######################################
    # Helpers
    ######################################

    def get_input(self):
        return self.input

    def fix_window_width(self):
        """
        Add 2px to the window width if GTK+ >= 3.20
        Because of the bug in <3.20 that doesn't add css borders to the width
        """
        if gtk_version_is_gte(3, 20, 0):
            width, height = self.get_size_request()
            self.set_size_request(width + 2, height)

    def init_theme(self):
        load_available_themes()
        theme = Theme.get_current()
        theme.clear_cache()
        self.init_styles(theme.compile_css())

    def activate_preferences(self, page='preferences'):
        """
        From the PyGTK Reference manual
        Say for example the preferences dialog is currently open,
        and the user chooses Preferences from the menu a second time;
        use the present() method to move the already-open dialog
        where the user can see it.
        """
        self.hide()

        if self.preferences_dialog is not None:
            logger.debug('show existing preferences_dialog')
            self.preferences_dialog.present(page=page)
        elif self.PreferencesDialog is not None:
            logger.debug('create new preferences_dialog')
            self.preferences_dialog = self.PreferencesDialog()  # pylint: disable=E1102
            self.preferences_dialog.connect('destroy', self.on_preferences_dialog_destroyed)
            self.preferences_dialog.show(page=page)
        # destroy command moved into dialog to allow for a help button

    def position_window(self):
        window_width = self.get_size()[0]
        current_screen = get_current_screen_geometry()

        # The topmost pixel of the window should be at 1/5 of the current screen's height
        # Window should be positioned in the center horizontally
        # Also, add offset x and y, in order to move window to the current screen
        self.move(current_screen['width'] / 2 - window_width / 2 + current_screen['x'],
                  current_screen['height'] / 5 + current_screen['y'])

    def show_window(self):
        # works only when the following methods are called in that exact order
        self.position_window()
        self.window.set_sensitive(True)
        self.window.present()
        if not is_wayland_compatibility_on():
            self.present_with_time(Keybinder.get_current_event_time())

        if not self.input.get_text():
            # make sure frequent apps are shown if necessary
            self.show_results([])
        elif self.settings.get_property('clear-previous-query'):
            self.input.set_text('')
        else:
            self.input.grab_focus()

    def toggle_window(self, key=None):
        self.hide() if self.is_visible() else self.show_window()

    def bind_show_app_hotkey(self, accel_name):
        if is_wayland_compatibility_on():
            return

        if self._current_accel_name == accel_name:
            return

        if self._current_accel_name:
            Keybinder.unbind(self._current_accel_name)
            self._current_accel_name = None

        logger.info("Trying to bind app hotkey: %s" % accel_name)
        Keybinder.bind(accel_name, self.toggle_window)
        self._current_accel_name = accel_name
        self.notify_hotkey_change(accel_name)

    def notify_hotkey_change(self, accel_name):
        (key, mode) = Gtk.accelerator_parse(accel_name)
        display_name = Gtk.accelerator_get_label(key, mode)
        app_cache_db = AppCacheDb.get_instance()
        if not app_cache_db.find('startup_hotkey_notification'):
            show_notification("Ulauncher", "Hotkey is set to %s" % display_name)
            app_cache_db.put('startup_hotkey_notification', True)
            app_cache_db.commit()

    def _get_user_query(self):
        # get_text() returns str, so we need to convert it to unicode
        return Query(force_unicode(self.input.get_text()))

    def select_result_item(self, index, onHover=False):
        if time.time() - self._results_render_time > 0.1:
            # Work around issue #23 -- don't automatically select item if cursor is hovering over it upon render
            self.results_nav.select(index)

    def enter_result_item(self, index=None, alt=False):
        if not self.results_nav.enter(self._get_user_query(), index, alt=alt):
            # hide the window if it has to be closed on enter
            self.hide_and_clear_input()

    def hide_and_clear_input(self):
        self.input.set_text('')
        self.hide()

    def show_results(self, result_items):
        """
        :param list result_items: list of ResultItem instances
        """
        try: self.appchooser
        except: self.appchooser = None

        # first time appchooser does not yet exist 
        if self.appchooser is not None:
            self.result_box_parent.remove(self.appchooser)

        self.results_nav = None
        self.result_box.foreach(lambda w: w.destroy())

        if not result_items and not self.input.get_text() and self.settings.get_property('show-recent-apps'):
            result_items = AppStatDb.get_instance().get_most_frequent(3)

        results = self.create_item_widgets(result_items, self._get_user_query())

        if results:
            self._results_render_time = time.time()
            map(self.result_box.add, results)
            self.results_nav = ItemNavigation(self.result_box.get_children())
            self.results_nav.select_default(self._get_user_query())

            self.result_box.show_all()
            self.result_box.set_margin_bottom(10)
            self.result_box.set_margin_top(3)
            self.apply_css(self.result_box)
        else:
            self.result_box.set_margin_bottom(0)
            self.result_box.set_margin_top(0)
        logger.debug('render %s results' % len(results))

    def show_appchooser(self, filepath):
        """
        :param str filepath: list of application
        """

        self.results_nav = None
        self.result_box.foreach(lambda w: w.destroy())

        def app_activated(self, widget):
            # need to get instance to be able to hide window later (is this okay?)
            window = UlauncherWindow.get_instance()
            exe = widget.get_executable()
            subprocess.Popen([exe, filepath])
            self.destroy()
            if window.is_visible():
                window.hide()

        mime = mimetypes.guess_type(filepath)[0]
        appchooser = Gtk.AppChooserWidget.new(mime)
        self.result_box_parent.add(appchooser)
        appchooser.connect("application-activated", app_activated)
        self.show_all()


    @staticmethod
    def create_item_widgets(items, query):
        results = []
        for index, result_item in enumerate(items):
            glade_filename = get_data_file('ui', '%s.ui' % result_item.UI_FILE)
            if not os.path.exists(glade_filename):
                glade_filename = None

            builder = Gtk.Builder()
            builder.set_translation_domain('ulauncher')
            builder.add_from_file(glade_filename)

            item_frame = builder.get_object('item-frame')
            item_frame.initialize(builder, result_item, index, query)

            results.append(item_frame)

        return results
