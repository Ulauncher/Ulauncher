# -*- Mode: Python; coding: utf-8; indent-tabs-mode: nil; tab-width: 4 -*-

import logging
import threading
from gi.repository import Gtk, Gdk, Keybinder

from ulauncher.helpers import singleton
from ulauncher.utils.display import get_current_screen_geometry
from ulauncher.config import get_data_file
from ulauncher.ui import create_item_widgets

# this import is needed for Gtk to find AppResultItemWidget class
from ulauncher.ui.AppResultItemWidget import AppResultItemWidget

from ulauncher.ui.ItemNavigation import ItemNavigation
from ulauncher.search import discover_search_modes, start_search
from ulauncher.search.apps.app_watcher import start as start_app_watcher
from ulauncher.search.UserQueryDb import UserQueryDb
from ulauncher.utils.Settings import Settings
from .WindowBase import WindowBase
from .AboutUlauncherDialog import AboutUlauncherDialog
from .PreferencesUlauncherDialog import PreferencesUlauncherDialog

logger = logging.getLogger(__name__)


class UlauncherWindow(WindowBase):
    __gtype_name__ = "UlauncherWindow"
    __current_accel_name = None

    @classmethod
    @singleton
    def get_instance(cls):
        return cls()

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

        self.search_modes = discover_search_modes()

        self.position_window()
        self.init_styles()
        self.bind_show_app_hotkey(Settings.get_instance().get_property('hotkey-show-app'))
        start_app_watcher()
        Keybinder.init()

    def position_window(self):
        window_width = self.get_size()[0]
        current_screen = get_current_screen_geometry()

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

    def get_user_query(self):
        return self.input.get_text().strip()

    def on_input_changed(self, entry):
        """
        Triggered by user input
        """
        start_search(self.get_user_query(), self.search_modes)

    def select_result_item(self, index):
        self.results_nav.select(index)

    def enter_result_item(self, index=None):
        if not self.results_nav.enter(self.get_user_query(), index):
            # close the window if it has to be closed on enter
            self.hide()
            self.save_user_query()

    def show_results(self, result_items):
        """
        :param list result_items: list of ResultItem instances
        """
        self.results_nav = None
        self.result_box.foreach(lambda w: w.destroy())
        results = list(create_item_widgets(result_items, self.get_user_query()))  # generator -> list
        if results:
            map(self.result_box.add, results)
            self.result_box.show_all()
            self.result_box.set_margin_bottom(10)
            self.results_nav = ItemNavigation(self.result_box.get_children())

            # select the same item user previously selected for this query
            user_queries = UserQueryDb.get_instance()
            name = user_queries.find(self.get_user_query())
            selected_index = self.results_nav.get_index_by_name(name) or 0 if name else 0
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
                self.enter_result_item()
            elif alt and keyname.isdigit() and 0 < int(keyname) < 10:
                # on Alt+<num>
                try:
                    self.enter_result_item(int(keyname) - 1)
                except IndexError:
                    # selected non-existing result item
                    pass

        if keyname == 'Escape':
            self.hide()

    def save_user_query(self):
        name = self.results_nav.get_selected_name()
        if name:
            user_queries = UserQueryDb.get_instance()
            user_queries.put(self.get_user_query(), name)
            user_queries.commit()  # save to disk
