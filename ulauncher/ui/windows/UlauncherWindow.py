# -*- Mode: Python; coding: utf-8; indent-tabs-mode: nil; tab-width: 4 -*-
import logging
from gi.repository import Gtk, Gdk, Keybinder  # type: ignore[attr-defined]

# pylint: disable=unused-import
# these imports are needed for Gtk to find widget classes
from ulauncher.ui.ResultWidget import ResultWidget  # noqa: F401
from ulauncher.ui.LayerShell import LayerShellOverlay
from ulauncher.config import PATHS
from ulauncher.ui.ItemNavigation import ItemNavigation
from ulauncher.modes.ModeHandler import ModeHandler
from ulauncher.modes.apps.AppResult import AppResult
from ulauncher.utils.Settings import Settings
from ulauncher.utils.wm import get_monitor
from ulauncher.utils.icon import load_icon_surface
from ulauncher.utils.environment import IS_X11_COMPATIBLE
from ulauncher.utils.Theme import Theme

logger = logging.getLogger()


class UlauncherWindow(Gtk.ApplicationWindow, LayerShellOverlay):
    _css_provider = None
    _drag_start_coords = None
    results_nav = None
    settings = Settings.load()

    def __init__(self, **kwargs):
        super().__init__(
            decorated=False,
            deletable=False,
            has_focus=True,
            icon_name="ulauncher",
            resizable=False,
            skip_pager_hint=True,
            skip_taskbar_hint=True,
            title="Ulauncher - Application Launcher",
            urgency_hint=True,
            window_position="center",
            **kwargs,
        )

        if LayerShellOverlay.is_supported():
            self.enable_layer_shell()

        # Try setting a transparent background
        screen = self.get_screen()
        visual = screen.get_rgba_visual()
        window_margin = 20
        if visual is None:
            logger.debug("Screen does not support alpha channels")
            visual = screen.get_system_visual()
            window_margin = 0

        self.set_visual(visual)

        # This box exists only for setting the margin conditionally, based on ^
        # without the theme being able to override it
        window_frame = Gtk.Box(
            margin_top=window_margin,
            margin_bottom=window_margin,
            margin_start=window_margin,
            margin_end=window_margin,
        )
        self.add(window_frame)

        window_container = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            app_paintable=True,
        )
        window_frame.pack_start(window_container, True, True, 0)

        event_box = Gtk.EventBox()
        input_box = Gtk.Box()
        event_box.add(input_box)

        self.input = Gtk.Entry(
            can_default=True,
            can_focus=True,
            has_focus=True,
            is_focus=True,
            height_request=30,
            margin_top=15,
            margin_bottom=15,
            margin_start=20,
            margin_end=20,
            receives_default=True,
        )

        prefs_btn = Gtk.Button(
            name="prefs_btn",
            width_request=24,
            height_request=24,
            receives_default=False,
            halign="center",
            valign="center",
            margin_end=15,
        )

        input_box.pack_start(self.input, True, True, 0)
        input_box.pack_end(prefs_btn, False, False, 0)

        self.scroll_container = Gtk.ScrolledWindow(
            can_focus=True,
            max_content_height=500,
            hscrollbar_policy="never",
            propagate_natural_height=True,
            shadow_type="in",
        )
        self.result_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.scroll_container.add(self.result_box)

        window_container.pack_start(event_box, True, True, 0)
        window_container.pack_end(self.scroll_container, True, True, 0)

        window_container.get_style_context().add_class("app")
        self.input.get_style_context().add_class("input")
        prefs_btn.get_style_context().add_class("prefs-btn")
        self.result_box.get_style_context().add_class("result-box")

        prefs_icon_surface = load_icon_surface(f"{PATHS.ASSETS}/icons/gear.svg", 16, self.get_scale_factor())
        prefs_btn.set_image(Gtk.Image.new_from_surface(prefs_icon_surface))
        window_frame.show_all()

        self.connect("focus-in-event", self.on_focus_in)
        self.connect("focus-out-event", self.on_focus_out)
        event_box.connect("button-press-event", self.on_mouse_down)
        self.input.connect("changed", self.on_input_changed)
        self.input.connect("key-press-event", self.on_input_key_press)
        prefs_btn.connect("clicked", lambda *_: self.app.show_preferences())

        self.set_keep_above(True)
        self.position_window()
        self.apply_theme()

        # this will trigger to show frequent apps if necessary
        self.show_results([])

    ######################################
    # GTK Signal Handlers
    ######################################

    def on_focus_out(self, *_):
        self.hide()

    def on_focus_in(self, *args):
        if self.settings.grab_mouse_pointer:
            ptr_dev = self.get_pointer_device()
            result = ptr_dev.grab(
                self.get_window(), Gdk.GrabOwnership.NONE, True, Gdk.EventMask.ALL_EVENTS_MASK, None, 0
            )
            logger.debug("Focus in event, grabbing pointer: %s", result)

    def on_input_changed(self, _):
        """
        Triggered by user input
        """
        self.app._query = self.input.get_text().lstrip()
        if self.is_visible():
            # input_changed can trigger when hiding window
            ModeHandler.get_instance().on_query_change(self.app.query)

    def on_input_key_press(self, widget, event):
        keyval = event.get_keyval()
        keyname = Gdk.keyval_name(keyval[1])
        alt = event.state & Gdk.ModifierType.MOD1_MASK
        ctrl = event.state & Gdk.ModifierType.CONTROL_MASK
        jump_keys = self.settings.get_jump_keys()
        ModeHandler.get_instance().on_key_press_event(widget, event, self.app.query)

        if keyname == "Escape":
            self.hide()

        elif ctrl and keyname == "comma":
            self.app.show_preferences()

        elif self.results_nav:
            if keyname in ("Up", "ISO_Left_Tab") or (ctrl and keyname == "p"):
                self.results_nav.go_up()
                return True
            if keyname in ("Down", "Tab") or (ctrl and keyname == "n"):
                self.results_nav.go_down()
                return True
            if alt and keyname in ("Return", "KP_Enter"):
                self.enter_result(alt=True)
            elif keyname in ("Return", "KP_Enter"):
                self.enter_result()
            elif alt and keyname in jump_keys:
                # on Alt+<num/letter>
                try:
                    self.select_result(jump_keys.index(keyname))
                except IndexError:
                    # selected non-existing result item
                    pass

        return False

    def on_mouse_down(self, _, event):
        """
        Move the window on drag
        """
        if event.button == 1:
            self.begin_move_drag(event.button, event.x_root, event.y_root, event.time)

    ######################################
    # Helpers
    ######################################

    @property
    def app(self):
        return self.get_application()

    def apply_css(self, widget):
        Gtk.StyleContext.add_provider(
            widget.get_style_context(), self._css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )
        if isinstance(widget, Gtk.Container):
            widget.forall(self.apply_css)

    def apply_theme(self):
        if not self._css_provider:
            self._css_provider = Gtk.CssProvider()
        self._css_provider.load_from_data(Theme.load(self.settings.theme_name).get_css().encode())
        self.apply_css(self)
        # pylint: disable=no-member
        visual = self.get_screen().get_rgba_visual()
        if visual:
            self.set_visual(visual)

    def position_window(self):
        monitor = get_monitor(self.settings.render_on_screen != "default-monitor")
        geo = monitor.get_geometry()
        max_height = geo.height - (geo.height * 0.15) - 100  # 100 is roughly the height of the text input
        window_width = 750
        pos_x = geo.width * 0.5 - window_width * 0.5 + geo.x
        pos_y = geo.y + geo.height * 0.12
        self.set_property("width-request", window_width)
        self.scroll_container.set_property("max-content-height", max_height)

        if self.layer_shell_enabled:
            self.set_vertical_position(pos_y)
        else:
            self.move(pos_x, pos_y)

    # pylint: disable=arguments-differ; https://gitlab.gnome.org/GNOME/pygobject/-/issues/231
    def show(self):
        # works only when the following methods are called in that exact order
        self.present()
        self.position_window()
        if IS_X11_COMPATIBLE:
            self.present_with_time(Keybinder.get_current_event_time())

        if not self.app.query:
            # make sure frequent apps are shown if necessary
            self.show_results([])

        self.input.grab_focus_without_selecting()
        super().show()

    # pylint: disable=arguments-differ; https://gitlab.gnome.org/GNOME/pygobject/-/issues/231
    def hide(self, *args, **kwargs):
        """Override the hide method to ensure the pointer grab is released."""
        if self.settings.grab_mouse_pointer:
            self.get_pointer_device().ungrab(0)
        super().hide(*args, **kwargs)
        if self.settings.clear_previous_query:
            self.app.query = ""

    def select_result(self, index):
        self.results_nav.select(index)

    def enter_result(self, index=None, alt=False):
        if self.results_nav.enter(self.app.query, index, alt=alt):
            # hide the window if it has to be closed on enter
            self.hide_and_clear_input()

    def get_pointer_device(self):
        return self.get_window().get_display().get_device_manager().get_client_pointer()

    def hide_and_clear_input(self):
        self.input.set_text("")
        self.hide()

    def show_results(self, results):
        """
        :param list results: list of Result instances
        """
        self.results_nav = None
        self.result_box.foreach(lambda w: w.destroy())

        limit = len(self.settings.get_jump_keys()) or 25
        if not self.input.get_text() and self.settings.max_recent_apps:
            results = AppResult.get_most_frequent(self.settings.max_recent_apps)

        results = self.create_item_widgets(results, self.app.query)

        if results:
            for item in results[:limit]:
                self.result_box.add(item)
            self.results_nav = ItemNavigation(self.result_box.get_children())
            self.results_nav.select_default(self.app.query)

            self.result_box.set_margin_bottom(10)
            self.result_box.set_margin_top(3)
            self.apply_css(self.result_box)
            self.scroll_container.show_all()
        else:
            # Hide the scroll container when there are no results since it normally takes up a
            # minimum amount of space even if it is empty.
            self.scroll_container.hide()
        logger.debug("render %s results", len(results))

    @staticmethod
    def create_item_widgets(items, query):
        results = []
        for index, result in enumerate(items):
            builder = Gtk.Builder()
            builder.set_translation_domain("ulauncher")
            builder.add_from_file(f"{PATHS.ASSETS}/ui/result.ui")

            item_frame = builder.get_object("item-frame")
            item_frame.initialize(builder, result, index, query)

            results.append(item_frame)

        return results
