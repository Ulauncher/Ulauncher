from __future__ import annotations

import logging
from typing import Any, Sequence

from gi.repository import Gdk, GLib, Gtk

import ulauncher
from ulauncher.config import paths
from ulauncher.internals.result import Result
from ulauncher.ui import layer_shell
from ulauncher.utils.eventbus import EventBus
from ulauncher.utils.load_icon_surface import load_icon_surface
from ulauncher.utils.settings import Settings
from ulauncher.utils.theme import Theme
from ulauncher.utils.wm import get_monitor

logger = logging.getLogger()
events = EventBus("window", True)


class UlauncherWindow(Gtk.ApplicationWindow):
    _css_provider: Gtk.CssProvider | None = None
    results_nav: ulauncher.ui.item_navigation.ItemNavigation | None = None
    is_dragging = False
    layer_shell_enabled = False
    settings = Settings.load()

    def __init__(self, **kwargs: Any) -> None:  # noqa: PLR0915
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
            window_position=Gtk.WindowPosition.CENTER,
            **kwargs,
        )

        events.set_self(self)

        if layer_shell.is_supported():
            self.layer_shell_enabled = layer_shell.enable(self)

        # This box exists only for setting the margin conditionally, based on ^
        # without the theme being able to override it
        self.window_frame = Gtk.Box()
        self.add(self.window_frame)

        window_container = Gtk.Box(app_paintable=True, orientation=Gtk.Orientation.VERTICAL)
        self.window_frame.pack_start(window_container, True, True, 0)

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
            halign=Gtk.Align.CENTER,
            valign=Gtk.Align.CENTER,
            margin_end=15,
        )

        input_box.pack_start(self.input, True, True, 0)
        input_box.pack_end(prefs_btn, False, False, 0)

        self.scroll_container = Gtk.ScrolledWindow(
            can_focus=True,
            max_content_height=500,
            hscrollbar_policy=Gtk.PolicyType.NEVER,
            propagate_natural_height=True,
            shadow_type=Gtk.ShadowType.IN,
        )
        self.result_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.scroll_container.add(self.result_box)

        window_container.pack_start(event_box, True, True, 0)
        window_container.pack_end(self.scroll_container, True, True, 0)

        window_container.get_style_context().add_class("app")
        self.input.get_style_context().add_class("input")
        prefs_btn.get_style_context().add_class("prefs-btn")
        self.result_box.get_style_context().add_class("result-box")

        prefs_icon_surface = load_icon_surface(f"{paths.ASSETS}/icons/gear.svg", 16, self.get_scale_factor())
        prefs_btn.set_image(Gtk.Image.new_from_surface(prefs_icon_surface))
        self.window_frame.show_all()

        self.connect("focus-in-event", lambda *_: self.on_focus_in())
        self.connect("focus-out-event", lambda *_: self.on_focus_out())
        event_box.connect("button-press-event", self.on_mouse_down)
        self.connect("button-release-event", lambda *_: self.on_mouse_up())
        self.input.connect("changed", lambda *_: self.on_input_changed())
        self.input.connect("key-press-event", self.on_input_key_press)
        prefs_btn.connect("clicked", lambda *_: events.emit("app:show_preferences"))

        self.set_keep_above(True)
        # Try setting a transparent background
        screen = self.get_screen()
        visual = screen.get_rgba_visual()
        composited = screen.is_composited()
        logger.debug("Screen RGBA visual: %s", visual)
        logger.debug("Screen is composited: %s", composited)
        shadow_size = 20 if composited else 0
        self.window_frame.set_properties(
            margin_top=shadow_size,
            margin_bottom=shadow_size,
            margin_start=shadow_size,
            margin_end=shadow_size,
        )
        if visual is None:
            logger.info("Screen does not support alpha channels. Likely not running a compositor.")
            visual = screen.get_system_visual()

        self.set_visual(visual)
        self.apply_theme()
        self.position_window()

        self.present()
        # note: present_with_time is needed on some DEs to defeat focus stealing protection
        # (Gnome 3 forks like Cinnamon or Budgie, but not Gnome 3 itself any longer)
        # The correct time to use is the time of the user interaction requesting the focus, but we don't have access
        # to that, so we use `Gdk.CURRENT_TIME`, which is the same as passing 0.
        self.present_with_time(Gdk.CURRENT_TIME)
        super().show()

        if self.query:
            self.set_input(self.query)
        else:
            # this will trigger to show frequent apps if necessary
            self.show_results([])

        GLib.idle_add(self.init_listeners)

    def init_listeners(self) -> None:
        from ulauncher.modes import mode_handler

        mode_handler.refresh_triggers()
        if self.query:
            mode_handler.on_query_change(self.query)

    ######################################
    # GTK Signal Handlers
    ######################################

    def on_focus_out(self) -> None:
        if self.settings.close_on_focus_out and not self.is_dragging:
            self.close(save_query=True)

    def on_focus_in(self) -> None:
        if self.settings.grab_mouse_pointer:
            self.toggle_grab_pointer_device(True)

    def on_input_changed(self) -> None:
        """
        Triggered by user input
        """
        events.emit("app:set_query", self.input.get_text(), update_input=False)
        from ulauncher.modes import mode_handler

        mode_handler.on_query_change(self.query)

    def on_input_key_press(self, entry_widget: Gtk.Entry, event: Gdk.EventKey) -> bool:  # noqa: PLR0911
        """
        Triggered by user key press
        Return True to stop other handlers from being invoked for the event
        """
        keyname = Gdk.keyval_name(event.keyval)
        alt = bool(event.state & Gdk.ModifierType.MOD1_MASK)
        ctrl = bool(event.state & Gdk.ModifierType.CONTROL_MASK)
        jump_keys = self.settings.get_jump_keys()

        use_arrow_key_aliases = len(self.settings.arrow_key_aliases) == 4  # noqa: PLR2004
        arrow_key_aliases = [*self.settings.arrow_key_aliases] if use_arrow_key_aliases else [None] * 4
        left_alias, down_alias, up_alias, right_alias = arrow_key_aliases
        if not use_arrow_key_aliases:
            logger.warning(
                "Invalid value for arrow_key_aliases: %s, expected four letters", self.settings.arrow_key_aliases
            )

        if keyname == "Escape":
            self.close(save_query=True)
            return True

        if ctrl and keyname == "comma":
            events.emit("app:show_preferences")
            return True

        if (
            keyname == "BackSpace"
            and not ctrl
            and not entry_widget.get_selection_bounds()
            and entry_widget.get_position() == len(self.query)
        ):
            from ulauncher.modes import mode_handler

            new_query = mode_handler.on_query_backspace(self.query)
            if new_query is not None:
                events.emit("app:set_query", new_query)
                return True

        if self.results_nav:
            if keyname in ("Up", "ISO_Left_Tab") or (ctrl and keyname == up_alias):
                self.results_nav.go_up()
                return True

            if keyname in ("Down", "Tab") or (ctrl and keyname == down_alias):
                self.results_nav.go_down()
                return True

            if ctrl and keyname == left_alias:
                entry_widget.set_position(max(0, entry_widget.get_position() - 1))
                return True

            if ctrl and keyname == right_alias:
                entry_widget.set_position(entry_widget.get_position() + 1)
                return True

            if keyname in ("Return", "KP_Enter"):
                self.results_nav.activate(self.query, alt=alt)
                return True
            if alt and event.string in jump_keys:
                self.select_result(jump_keys.index(event.string))
                return True
        return False

    def on_mouse_down(self, _event_box: Gtk.EventBox, event: Gdk.EventButton) -> None:
        """
        Move the window on drag
        """
        if event.button == 1 and event.type == Gdk.EventType.BUTTON_PRESS:
            self.is_dragging = True
            self.begin_move_drag(event.button, int(event.x_root), int(event.y_root), event.time)

    def on_mouse_up(self) -> None:
        self.is_dragging = False

    ######################################
    # Helpers
    ######################################

    @property
    def query(self) -> str:
        return self.get_application().query  # type: ignore[no-any-return, union-attr]

    def apply_css(self, widget: Gtk.Widget) -> None:
        assert self._css_provider
        Gtk.StyleContext.add_provider(
            widget.get_style_context(), self._css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )
        if isinstance(widget, Gtk.Container):
            widget.forall(self.apply_css)

    def apply_theme(self) -> None:
        if not self._css_provider:
            self._css_provider = Gtk.CssProvider()
        theme_css = Theme.load(self.settings.theme_name).get_css().encode()
        self._css_provider.load_from_data(theme_css)
        self.apply_css(self)
        visual = self.get_screen().get_rgba_visual()
        if visual:
            self.set_visual(visual)

    def position_window(self) -> None:
        monitor = get_monitor(self.settings.render_on_screen != "default-monitor")
        if monitor:
            geo = monitor.get_geometry()
            max_height = geo.height - (geo.height * 0.15) - 100  # 100 is roughly the height of the text input
            window_width = self.settings.base_width
            pos_x = int(geo.width * 0.5 - window_width * 0.5 + geo.x)
            pos_y = int(geo.y + geo.height * 0.12)
            self.set_property("width-request", window_width)
            self.scroll_container.set_property("max-content-height", max_height)

            if self.layer_shell_enabled:
                layer_shell.set_vertical_position(self, pos_y)
            else:
                self.move(pos_x, pos_y)

    @events.on
    def close(self, save_query: bool = False) -> None:
        if not save_query or self.settings.clear_previous_query:
            events.emit("app:set_query", "", update_input=False)
        if self.settings.grab_mouse_pointer:
            self.toggle_grab_pointer_device(False)
        super().close()
        events.set_self(None)
        self.destroy()

    def select_result(self, index: int) -> None:
        if self.results_nav:
            self.results_nav.select(index)

    def toggle_grab_pointer_device(self, grab: bool) -> None:
        window = self.get_window()
        device_manager = window and window.get_display().get_device_manager()
        pointer_device = device_manager and device_manager.get_client_pointer()
        if not (window and device_manager and pointer_device):
            logger.warning("Could not get the pointer device.")
            return

        if not grab:
            pointer_device.ungrab(0)
            return

        grab_status = pointer_device.grab(window, Gdk.GrabOwnership.NONE, True, Gdk.EventMask.ALL_EVENTS_MASK, None, 0)
        logger.debug("Focus in event, grabbing pointer: %s", grab_status)

    @events.on
    def set_input(self, query_str: str) -> None:
        self.input.set_text(query_str)
        self.input.set_position(-1)

    @events.on
    def show_results(self, results: Sequence[Result]) -> None:
        self.results_nav = None
        self.result_box.foreach(lambda w: w.destroy())

        limit = len(self.settings.get_jump_keys()) or 25
        if not self.input.get_text() and self.settings.max_recent_apps:
            from ulauncher.modes.apps.app_result import AppResult

            results = AppResult.get_most_frequent(self.settings.max_recent_apps)

        if results:
            from ulauncher.ui.result_widget import ResultWidget

            result_widgets: list[ResultWidget] = []
            for index, result in enumerate(results[:limit]):
                result_widget = ResultWidget(result, index, self.query)
                result_widgets.append(result_widget)
                self.result_box.add(result_widget)
            from ulauncher.ui.item_navigation import ItemNavigation

            self.results_nav = ItemNavigation(result_widgets)
            self.results_nav.select_default(self.query)

            self.result_box.set_margin_bottom(10)
            self.result_box.set_margin_top(3)
            self.apply_css(self.result_box)
            self.scroll_container.show_all()
        else:
            # Hide the scroll container when there are no results since it normally takes up a
            # minimum amount of space even if it is empty.
            self.scroll_container.hide()
        logger.debug("render %s results", len(results))
