# -*- Mode: Python; coding: utf-8; indent-tabs-mode: nil; tab-width: 4 -*-
import os
import logging

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
gi.require_version('Keybinder', '3.0')

# pylint: disable=wrong-import-position, unused-argument
from gi.repository import Gtk, Gdk, Keybinder

# pylint: disable=unused-import
# these imports are needed for Gtk to find widget classes
from ulauncher.ui.ResultWidget import ResultWidget  # noqa: F401
from ulauncher.ui.SmallResultWidget import SmallResultWidget   # noqa: F401

from ulauncher.config import get_asset
from ulauncher.ui.ItemNavigation import ItemNavigation
from ulauncher.modes.ModeHandler import ModeHandler
from ulauncher.modes.apps.AppResult import AppResult
from ulauncher.utils.Settings import Settings
from ulauncher.utils.decorator.singleton import singleton
from ulauncher.utils.timer import timer
from ulauncher.utils.wm import get_monitor, get_scaling_factor
from ulauncher.utils.icon import load_icon
from ulauncher.utils.environment import IS_X11_COMPATIBLE
from ulauncher.utils.Theme import Theme, load_available_themes
from ulauncher.modes.Query import Query

logger = logging.getLogger()


@Gtk.Template(filename=get_asset("ui/ulauncher_window.ui"))
class UlauncherWindow(Gtk.ApplicationWindow):
    __gtype_name__ = "UlauncherWindow"
    input: Gtk.Entry  # These have to be declared on a separate line for some reason
    prefs_btn: Gtk.Button
    result_box: Gtk.Box
    scroll_container: Gtk.ScrolledWindow
    window_body: Gtk.Box

    input = Gtk.Template.Child("input")
    prefs_btn = Gtk.Template.Child("prefs_btn")
    result_box = Gtk.Template.Child("result_box")
    scroll_container = Gtk.Template.Child("result_box_scroll_container")
    window_body = Gtk.Template.Child("body")
    results_nav = None
    settings = Settings.get_instance()
    is_focused = False
    initial_query = None
    _css_provider = None
    _drag_start_coords = None

    @classmethod
    @singleton
    def get_instance(cls):
        return cls()

    ######################################
    # GTK Signal Handlers
    ######################################

    @Gtk.Template.Callback()
    def on_focus_out(self, widget, event):
        # apparently Gtk doesn't provide a mechanism to tell if window is in focus
        # this is a simple workaround to avoid hiding window
        # when user hits Alt+key combination or changes input source, etc.
        self.is_focused = False
        timer(0.07, lambda: self.is_focused or self.hide())

    @Gtk.Template.Callback()
    def on_focus_in(self, *args):
        if self.settings.get_property('grab-mouse-pointer'):
            ptr_dev = self.get_pointer_device()
            result = ptr_dev.grab(
                self.get_window(),
                Gdk.GrabOwnership.NONE,
                True,
                Gdk.EventMask.ALL_EVENTS_MASK,
                None,
                0
            )
            logger.debug("Focus in event, grabbing pointer: %s", result)
        self.is_focused = True

    @Gtk.Template.Callback()
    def on_input_changed(self, entry):
        """
        Triggered by user input
        """
        query = self._get_user_query()
        # This might seem odd, but this makes sure any normalization done in get_user_query() is
        # reflected in the input box. In particular, stripping out the leading white-space.
        self.input.set_text(query)
        ModeHandler.get_instance().on_query_change(query)

    @Gtk.Template.Callback()
    def on_input_key_press(self, widget, event):
        keyval = event.get_keyval()
        keyname = Gdk.keyval_name(keyval[1])
        alt = event.state & Gdk.ModifierType.MOD1_MASK
        ctrl = event.state & Gdk.ModifierType.CONTROL_MASK
        jump_keys = self.settings.get_jump_keys()
        ModeHandler.get_instance().on_key_press_event(widget, event, self._get_user_query())

        if keyname == 'Escape':
            self.hide()

        elif ctrl and keyname == 'comma':
            self.show_preferences()

        elif self.results_nav:
            if keyname in ('Up', 'ISO_Left_Tab') or (ctrl and keyname == 'p'):
                self.results_nav.go_up()
                return True
            if keyname in ('Down', 'Tab') or (ctrl and keyname == 'n'):
                self.results_nav.go_down()
                return True
            if alt and keyname in ('Return', 'KP_Enter'):
                self.enter_result(alt=True)
            elif keyname in ('Return', 'KP_Enter'):
                self.enter_result()
            elif alt and keyname in jump_keys:
                # on Alt+<num/letter>
                try:
                    self.select_result(jump_keys.index(keyname))
                except IndexError:
                    # selected non-existing result item
                    pass

        return False

    ######################################
    # Helpers
    ######################################

    def get_input(self):
        return self.input

    def init_styles(self, path):
        if not self._css_provider:
            self._css_provider = Gtk.CssProvider()
        self._css_provider.load_from_path(path)
        self.apply_css(self)
        # pylint: disable=no-member
        visual = self.get_screen().get_rgba_visual()
        if visual:
            self.set_visual(visual)

    def apply_css(self, widget):
        Gtk.StyleContext.add_provider(widget.get_style_context(),
                                      self._css_provider,
                                      Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        if isinstance(widget, Gtk.Container):
            widget.forall(self.apply_css)

    def set_cursor(self, cursor_name):
        # pylint: disable=no-member
        window_ = self.get_window()
        cursor = Gdk.Cursor.new_from_name(window_.get_display(), cursor_name)
        window_.set_cursor(cursor)

    def init_theme(self):
        load_available_themes()
        theme = Theme.get_current()
        theme.clear_cache()

        if self.settings.get_property('disable-window-shadow'):
            self.window_body.get_style_context().add_class('no-window-shadow')

        self._render_prefs_icon()
        self.init_styles(theme.compile_css())

    @Gtk.Template.Callback()
    def show_preferences(self, *_):
        self.get_application().show_preferences()

    def position_window(self):
        monitor = get_monitor(self.settings.get_property('render-on-screen') != "default-monitor")
        geo = monitor.get_geometry()
        max_height = geo.height - (geo.height * 0.15) - 100  # 100 is roughly the height of the text input
        window_width = 500 * get_scaling_factor()
        self.set_property('width-request', window_width)
        self.scroll_container.set_property('max-content-height', max_height)
        self.move(geo.width * 0.5 - window_width * 0.5 + geo.x, geo.y + geo.height * 0.12)

    def show_window(self):
        # works only when the following methods are called in that exact order
        self.present()
        self.position_window()
        if IS_X11_COMPATIBLE:
            self.present_with_time(Keybinder.get_current_event_time())

        if self.initial_query:
            self.input.set_text(self.initial_query)
            self.input.set_position(len(self.initial_query))
            self.initial_query = None
        elif not self._get_input_text():
            # make sure frequent apps are shown if necessary
            self.show_results([])
        elif self.settings.get_property('clear-previous-query'):
            self.input.set_text('')
        else:
            self.input.grab_focus()

    @Gtk.Template.Callback()
    def on_mouse_down(self, _, event):
        """
        Prepare moving the window if the user drags
        """
        # Only on left clicks and not on the results
        if event.button == 1 and event.y < 100:
            self.set_cursor("grab")
            self._drag_start_coords = {'x': event.x, 'y': event.y}

    @Gtk.Template.Callback()
    def on_mouse_up(self, *_):
        """
        Clear drag to move event data
        """
        self._drag_start_coords = None
        self.set_cursor("default")

    @Gtk.Template.Callback()
    def on_mouse_move(self, _, event):
        """
        Move window if cursor is held
        """
        start = self._drag_start_coords
        if start and event.state == Gdk.ModifierType.BUTTON1_MASK:
            self.move(
                event.x_root - start['x'],
                event.y_root - start['y']
            )

    def _get_input_text(self):
        return self.input.get_text().lstrip()

    def _get_user_query(self):
        return Query(self._get_input_text())

    def select_result(self, index):
        self.results_nav.select(index)

    def enter_result(self, index=None, alt=False):
        if self.results_nav.enter(self._get_user_query(), index, alt=alt):
            # hide the window if it has to be closed on enter
            self.hide_and_clear_input()

    def hide(self, *args, **kwargs):
        """Override the hide method to ensure the pointer grab is released."""
        if self.settings.get_property('grab-mouse-pointer'):
            self.get_pointer_device().ungrab(0)
        super().hide(*args, **kwargs)

    def get_pointer_device(self):
        return (self
                .get_window()
                .get_display()
                .get_device_manager()
                .get_client_pointer())

    def hide_and_clear_input(self):
        self.input.set_text('')
        self.hide()

    def show_results(self, results):
        """
        :param list results: list of Result instances
        """
        self.results_nav = None
        self.result_box.foreach(lambda w: w.destroy())

        limit = len(self.settings.get_jump_keys()) or 25
        show_recent_apps = self.settings.get_property('show-recent-apps')
        recent_apps_number = int(show_recent_apps) if show_recent_apps.isnumeric() else 0
        if not self.input.get_text() and recent_apps_number > 0:
            results = AppResult.get_most_frequent(recent_apps_number)

        results = self.create_item_widgets(results, self._get_user_query())

        if results:
            for item in results[:limit]:
                self.result_box.add(item)
            self.results_nav = ItemNavigation(self.result_box.get_children())
            self.results_nav.select_default(self._get_user_query())

            self.result_box.set_margin_bottom(10)
            self.result_box.set_margin_top(3)
            self.apply_css(self.result_box)
            self.scroll_container.show_all()
        else:
            # Hide the scroll container when there are no results since it normally takes up a
            # minimum amount of space even if it is empty.
            self.scroll_container.hide()
        logger.debug('render %s results', len(results))

    def _render_prefs_icon(self):
        prefs_pixbuf = load_icon(get_asset('icons/gear.svg'), 16 * get_scaling_factor())
        prefs_image = Gtk.Image.new_from_pixbuf(prefs_pixbuf)
        self.prefs_btn.set_image(prefs_image)

    @staticmethod
    def create_item_widgets(items, query):
        results = []
        for index, result in enumerate(items):
            glade_filename = get_asset(f"ui/{result.UI_FILE}.ui")
            if not os.path.exists(glade_filename):
                glade_filename = None

            builder = Gtk.Builder()
            builder.set_translation_domain('ulauncher')
            builder.add_from_file(glade_filename)

            item_frame = builder.get_object('item-frame')
            item_frame.initialize(builder, result, index, query)

            results.append(item_frame)

        return results
