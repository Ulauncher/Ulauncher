from __future__ import annotations

import logging
from typing import Any, Iterable

from gi.repository import Gdk, GLib, Gtk

import ulauncher
from ulauncher import paths
from ulauncher.internals.result import Result
from ulauncher.modes.query_handler import QueryHandler
from ulauncher.ui import layer_shell
from ulauncher.utils.environment import DESKTOP_ID, IS_X11_COMPATIBLE
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
    query_handler = QueryHandler()

    def __init__(self, **kwargs: Any) -> None:  # noqa: PLR0915
        logger.info("Opening Ulauncher window")
        window_width = int(self.settings.base_width)

        # Use the full width of the monitor for the window, and center the visible window
        # needed because Gnome Wayland assumes you want to positions new windows next to
        # the topmost window if any, instead of centering it.
        if DESKTOP_ID == "GNOME" and not IS_X11_COMPATIBLE and (monitor_size := self.get_monitor_size()):
            window_width = monitor_size.width

        super().__init__(
            decorated=False,
            deletable=False,
            has_focus=True,
            icon_name="ulauncher",
            opacity=0,  # set to 0 so we can show the window and get keyboard input before it's fully loaded
            resizable=False,
            skip_pager_hint=True,
            skip_taskbar_hint=True,
            title="Ulauncher - Application Launcher",
            urgency_hint=True,
            window_position=Gtk.WindowPosition.CENTER,
            width_request=window_width,
            **kwargs,
        )

        events.set_self(self)

        # avoid checking layer shell support for known cases it does not apply (for performance reasons)
        if not IS_X11_COMPATIBLE and DESKTOP_ID != "GNOME" and layer_shell.is_supported():
            self.layer_shell_enabled = layer_shell.enable(self)
            if self.layer_shell_enabled:
                logger.info("Layer shell support is enabled")
            else:
                logger.warning(
                    "Layer shell is not supported. If you have issues with window positioning, "
                    "ensure that your compositor supports it and that you have installed the gtk-layer-shell library"
                )

        # This box exists only for setting the margin conditionally, based on ^
        # without the theme being able to override it
        self.window_frame = Gtk.Box()
        self.add(self.window_frame)

        self.window_container = Gtk.Box(app_paintable=True, orientation=Gtk.Orientation.VERTICAL)
        self.window_frame.pack_start(self.window_container, True, True, 0)

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

        self.prefs_btn = Gtk.Button(
            name="prefs_btn",
            width_request=24,
            height_request=24,
            receives_default=False,
            halign=Gtk.Align.CENTER,
            valign=Gtk.Align.CENTER,
            margin_end=15,
        )

        input_box.pack_start(self.input, True, True, 0)
        input_box.pack_end(self.prefs_btn, False, False, 0)

        self.scroll_container = Gtk.ScrolledWindow(
            can_focus=True,
            max_content_height=500,
            hscrollbar_policy=Gtk.PolicyType.NEVER,
            propagate_natural_height=True,
            shadow_type=Gtk.ShadowType.IN,
        )
        self.result_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.scroll_container.add(self.result_box)
        self.window_container.pack_end(self.scroll_container, True, True, 0)

        self.window_container.pack_start(event_box, True, True, 0)

        self.window_frame.show_all()

        self.connect("focus-in-event", lambda *_: self.on_focus_in())
        self.connect("focus-out-event", lambda *_: self.on_focus_out())
        event_box.connect("button-press-event", self.on_mouse_down)
        self.connect("button-release-event", lambda *_: self.on_mouse_up())
        self.input.connect("changed", lambda *_: self.on_input_changed())
        self.input.connect("key-press-event", self.on_input_key_press)
        self.connect("draw", self.on_initial_draw)
        self.prefs_btn.connect("clicked", lambda *_: events.emit("app:show_preferences"))

        # Try setting a transparent background
        screen = self.get_screen()
        visual = screen.get_rgba_visual()
        if visual is None:
            logger.info("Screen does not support alpha channels")
            visual = screen.get_system_visual()

        self.set_visual(visual)

        is_composited = screen.is_composited()
        logger.debug("Screen is composited: %s", is_composited)
        if not is_composited:
            # without a compositor deferred would lead to "flash of unstyled content"
            self.apply_styling()

        self.set_keep_above(True)
        self.present()
        # note: present_with_time is needed on some DEs to defeat focus stealing protection
        # (Gnome 3 forks like Cinnamon or Budgie, but not Gnome 3 itself any longer)
        # The correct time to use is the time of the user interaction requesting the focus, but we don't have access
        # to that, so we use `Gdk.CURRENT_TIME`, which is the same as passing 0.
        self.present_with_time(Gdk.CURRENT_TIME)
        super().show()

        if self.query_str:
            self.set_input(self.query_str)

    def apply_styling(self) -> None:
        """
        Apply styling and position the window.

        Note that this method is slow and should be called after the window is shown if possible.
        """
        if self.get_opacity() == 1:  # already applied styling
            return

        self.window_container.get_style_context().add_class("app")
        self.input.get_style_context().add_class("input")
        self.prefs_btn.get_style_context().add_class("prefs-btn")
        self.result_box.get_style_context().add_class("result-box")
        prefs_icon_surface = load_icon_surface(f"{paths.ASSETS}/icons/gear.svg", 16, self.get_scale_factor())
        self.prefs_btn.set_image(Gtk.Image.new_from_surface(prefs_icon_surface))

        self.apply_theme()
        self.position_window()
        self.set_opacity(1)

    def deferred_init(self) -> None:
        if self.query_str:
            # select all text in the input field.
            # used when user turns off "start with blank query" setting
            self.input.select_region(0, -1)
        else:
            # NOTE: this will show frequent apps if enabled (we should probably refactor this to avoid confusion)
            self.show_results([])
        self.apply_styling()
        self.query_handler.load_triggers(force=True)
        self.query_handler.update(self.query_str)

    ######################################
    # GTK Signal Handlers
    ######################################

    def on_initial_draw(self, *_: tuple[Any]) -> None:
        logger.info("Window shown")
        self.disconnect_by_func(self.on_initial_draw)
        GLib.idle_add(self.deferred_init)

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
        self.query_handler.update(self.query_str)

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
            and entry_widget.get_position() == len(self.query_str)
            and self.query_handler.handle_backspace(self.query_str)
        ):
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
                self.results_nav.activate(alt)
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
    def query_str(self) -> str:
        return self.get_application().query  # type: ignore[no-any-return, union-attr]

    def apply_css(self, widget: Gtk.Widget) -> None:
        if not self._css_provider:
            self._css_provider = Gtk.CssProvider()
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

    def get_monitor_size(self) -> Gdk.Rectangle | None:
        if monitor := get_monitor(self.settings.render_on_screen != "default-monitor"):
            return monitor.get_geometry()
        return None

    def position_window(self) -> None:
        margin_x = margin_y = 20.0

        if monitor_size := self.get_monitor_size():
            base_height = 100  # roughly the height of Ulauncher with no results
            window_width = self.settings.base_width
            max_height = monitor_size.height * 0.85 - base_height
            self.scroll_container.set_property("max-content-height", max_height)

            # Part II of the Gnome Wayland fix (see above in __init__)
            if DESKTOP_ID == "GNOME" and not IS_X11_COMPATIBLE:
                margin_x = (monitor_size.width - window_width) / 2

            else:
                pos_x = int(monitor_size.width * 0.5 - window_width * 0.5 + monitor_size.x)
                pos_y = int(monitor_size.y + monitor_size.height * 0.12)

                if self.layer_shell_enabled:
                    layer_shell.set_vertical_position(self, pos_y)
                else:
                    self.move(pos_x, pos_y)

        if self.is_composited():
            self.window_frame.set_properties(
                margin_top=margin_y,
                margin_bottom=margin_y,
                margin_start=margin_x,
                margin_end=margin_x,
            )

    def close(self, save_query: bool = False) -> None:
        logger.info("Closing Ulauncher window")
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
        if window := self.get_window():
            seat = window.get_display().get_default_seat()
            if not window or not seat:
                logger.warning("Could not get the pointer device.")
                return

            if not grab:
                seat.ungrab()
                return

            grab_status = seat.grab(window, Gdk.SeatCapabilities.ALL_POINTING, True)
            logger.debug("Focus in event, grabbing pointer: %s", grab_status)

    @events.on
    def set_input(self, query_str: str) -> None:
        self.input.set_text(query_str)
        self.input.set_position(-1)

    @events.on
    def show_results(self, results: Iterable[Result]) -> None:
        self.results_nav = None
        self.result_box.foreach(lambda w: w.destroy())

        limit = len(self.settings.get_jump_keys()) or 25
        if not self.input.get_text() and self.settings.max_recent_apps:
            results = self.query_handler.get_initial_results(self.settings.max_recent_apps)

        if results:
            from ulauncher.ui.result_widget import ResultWidget

            result_widgets: list[ResultWidget] = []
            for index, result in enumerate(results):
                if index >= limit:
                    break
                result_widget = ResultWidget(result, index, self.query_handler.query)
                result_widgets.append(result_widget)
                self.result_box.add(result_widget)
            from ulauncher.ui.item_navigation import ItemNavigation

            self.results_nav = ItemNavigation(self.query_handler, result_widgets)
            self.results_nav.select_default()

            self.result_box.set_margin_bottom(10)
            self.result_box.set_margin_top(3)
            self.apply_css(self.result_box)
            self.scroll_container.show_all()
            logger.debug("Render %s results", len(result_widgets))
        else:
            # Hide the scroll container when there are no results since it normally takes up a
            # minimum amount of space even if it is empty.
            self.scroll_container.hide()
            logger.debug("Hiding results container, no results found")
