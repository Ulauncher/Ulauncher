# -*- Mode: Python; coding: utf-8; indent-tabs-mode: nil; tab-width: 4 -*-

import logging
import threading
from gi.repository import Gtk, Gdk, Keybinder

from ulauncher_lib import Window
from ulauncher_lib.Display import display
from ulauncher_lib.ulauncherconfig import get_data_file
from ulauncher.AboutUlauncherDialog import AboutUlauncherDialog
from ulauncher.PreferencesUlauncherDialog import PreferencesUlauncherDialog
from . results.AppResultItem import AppResultItem  # this import is needed for Gtk to find AppResultItem class
from . results import find_apps
from . results.Navigation import Navigation
from . backend.apps import start_sync
from .backend.user_queries import db as db_user_queries
from service_locator import getSettings

logger = logging.getLogger(__name__)


class UlauncherWindow(Window):
    __gtype_name__ = "UlauncherWindow"
    __current_accel_name = None

    def get_widget(self, id):
        """
        Return widget instance by its ID
        """
        return self.builder.get_object(id)

    def finish_initializing(self, builder):
        """
        Set up the main window
        """
        super(UlauncherWindow, self).finish_initializing(builder)

        self.results_nav = None
        self.builder = builder
        self.window = self.get_widget('ulauncher_window')
        self.input = self.get_widget('input')
        self.prefs_btn = self.get_widget('prefs_btn')
        self.result_box = builder.get_object("result_box")

        self.input.connect('changed', self.on_input_changed)
        self.prefs_btn.connect('clicked', self.on_mnu_preferences_activate)

        self.set_keep_above(True)

        self.AboutDialog = AboutUlauncherDialog
        self.PreferencesDialog = PreferencesUlauncherDialog

        self.position_window()
        self.init_styles()
        self.bind_show_app_hotkey(getSettings().get_property('hotkey-show-app'))
        start_sync()
        Keybinder.init()

    def position_window(self):
        window_width = self.get_size()[0]
        current_screen = display.get_current_screen_geometry()

        # The topmost pixel of the window should be at 1/4 of the current screen's height
        # Window should be positioned in the center horizontally
        # Also, add offset x and y, in order to move window to the current screen
        self.move(current_screen['width'] / 2 - window_width / 2 + current_screen['x'],
                  current_screen['height'] / 4 + current_screen['y'])

    def init_styles(self):
        self.provider = Gtk.CssProvider()
        self.provider.load_from_path(get_data_file('ui', 'ulauncher.css'))
        self.apply_css(self, self.provider)
        self.screen = self.get_screen()
        self.visual = self.screen.get_rgba_visual()
        if self.visual is not None and self.screen.is_composited():
            self.set_visual(self.visual)

    def apply_css(self, widget, provider):
        Gtk.StyleContext.add_provider(widget.get_style_context(),
                                      provider,
                                      Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

        if isinstance(widget, Gtk.Container):
            widget.forall(self.apply_css, provider)

    def on_focus_out_event(self, widget, event):
        # apparently Gtk doesn't provide a mechanism to tell if window is in focus
        # this is a simple workaround to avoid hiding window
        # when user hits Alt+key combination or changes input source, etc.
        self.is_focused = False
        t = threading.Timer(0.07, lambda: self.is_focused or self.hide())
        t.start()

    def on_focus_in_event(self, *args):
        self.is_focused = True

    def show_window(self):
        # works only when the following methods are called in that exact order
        self.input.set_text('')
        self.position_window()
        self.window.set_sensitive(True)
        self.window.present()
        self.present_with_time(Keybinder.get_current_event_time())

    def cb_toggle_visibility(self, key):
        self.hide() if self.is_visible() else self.show_window()

    def bind_show_app_hotkey(self, accel_name):
        if self.__current_accel_name == accel_name:
            return

        if self.__current_accel_name:
            Keybinder.unbind(self.__current_accel_name)
            self.__current_accel_name = None

        logger.info("Trying to bind app hotkey: %s" % accel_name)
        Keybinder.bind(accel_name, self.cb_toggle_visibility)
        self.__current_accel_name = accel_name

    def on_input_changed(self, entry):
        """
        Triggered by user input
        """
        query = entry.get_text()
        self.on_results(find_apps(query))

    def select_result_item(self, index):
        self.results_nav.select(index)

    def enter_result_item(self):
        if self.results_nav.enter():
            self.hide()
            self.save_user_query()

    def on_results(self, results):
        self.results_nav = None
        self.result_box.foreach(lambda w: w.destroy())
        results = list(results)  # generator -> list
        if results:
            map(self.result_box.add, results)
            self.result_box.show_all()
            self.result_box.set_margin_bottom(10)
            self.results_nav = Navigation(self.result_box.get_children())

            selected_index = 0
            desktop_file = db_user_queries.find(self.input.get_text())
            if desktop_file:

                # try to get index of item by desktop file
                selected_index = self.results_nav.get_index_by_desktop_file(desktop_file) or 0

            self.results_nav.select(selected_index)
            self.apply_css(self.result_box, self.provider)
        else:
            self.result_box.set_margin_bottom(0)

    def on_key_press_event(self, widget, event):
        keyval = event.get_keyval()
        keyname = Gdk.keyval_name(keyval[1])
        alt = event.state & Gdk.ModifierType.MOD1_MASK

        if self.results_nav:
            if keyname == 'Up':
                self.results_nav.go_up()
            elif keyname == 'Down':
                self.results_nav.go_down()
            elif keyname in ('Return', 'KP_Enter'):
                if self.results_nav.enter():
                    self.hide()
                    self.save_user_query()
            elif alt and keyname.isdigit() and 0 < int(keyname) < 10:
                # on Alt+<num>
                try:
                    if self.results_nav.enter(int(keyname) - 1):
                        self.hide()
                except IndexError:
                    # selected non-existing result item
                    pass

        if keyname == 'Escape':
            self.hide()

    def save_user_query(self):

        desktop_file_path = self.results_nav.get_selected_desktop_file()
        if desktop_file_path:

            db_user_queries.put(self.input.get_text(), desktop_file_path)
            db_user_queries.commit()
