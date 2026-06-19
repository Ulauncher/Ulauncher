from __future__ import annotations

import logging
import os
import sys
import time
from typing import TYPE_CHECKING, Any, cast

from gi.repository import Gdk, Gtk

from ulauncher import paths
from ulauncher.internals.results_update import ResultsUpdate
from ulauncher.ui.helpers import layer_shell
from ulauncher.ui.helpers.monitor import get_monitor
from ulauncher.ui.helpers.theme import Theme
from ulauncher.ui.load_icon_surface import load_icon_surface
from ulauncher.ui.results_view import ResultsView
from ulauncher.utils import scheduling
from ulauncher.utils.environment import DESKTOP_ID, IS_X11_COMPATIBLE
from ulauncher.utils.eventbus import EventBus
from ulauncher.utils.settings import Settings

if TYPE_CHECKING:
    from ulauncher.ui.app import UlauncherApp

logger = logging.getLogger(__name__)
events = EventBus()


class UlauncherWindow(Gtk.ApplicationWindow):
    _css_provider: Gtk.CssProvider | None = None
    is_dragging = False
    layer_shell_enabled = False
    settings: Settings

    def __init__(self, **kwargs: Any) -> None:  # noqa: PLR0915
        logger.info("Opening Ulauncher window")
        self.settings = Settings.load(force=True)
        width_request = self.settings.base_width
        height_request = -1

        if DESKTOP_ID == "GNOME" and not IS_X11_COMPATIBLE and (monitor_size := self.get_monitor_size()):
            # Use the full width of the monitor for the window, and center the visible window
            # needed because Gnome Wayland assumes you want to positions new windows next to
            # the topmost window if any, instead of centering it.
            width_request = monitor_size.width
            height_request = monitor_size.height

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
            width_request=width_request,
            height_request=height_request,
            **kwargs,
        )
        # avoid checking layer shell support for known cases it does not apply (for performance reasons)
        if not IS_X11_COMPATIBLE and DESKTOP_ID != "GNOME" and self.settings.layer_shell and layer_shell.is_supported():
            self.layer_shell_enabled = layer_shell.enable(self)
            if self.layer_shell_enabled:
                logger.info("Layer shell support is enabled")
            else:
                logger.warning(
                    "Layer shell is not supported. If you have issues with window positioning, "
                    "ensure that your compositor supports it and that you have installed the gtk-layer-shell library"
                )

        # Widget structure
        #
        # frame (positioning container for Gnome, not affected by theme)
        # └── shadow_container (provides space for shadow when enabled)
        #     └── theme_root(.app)
        #         ├── drag_listener
        #         │   └── prompt
        #         │       ├── prompt_input (.input)
        #         │       └── prefs_btn (.prefs-btn)
        #         └── results_view (ScrolledWindow)
        #             └── results box (.result-box)
        #                 └── ResultWidget (multiple)

        self.frame = Gtk.Box(valign=Gtk.Align.START)
        self.add(self.frame)

        shadow_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, margin=self._get_shadow_size())
        self.frame.pack_start(shadow_container, True, True, 0)

        self.theme_root = Gtk.Box(app_paintable=True, orientation=Gtk.Orientation.VERTICAL)
        shadow_container.pack_start(self.theme_root, True, True, 0)

        self.prompt = Gtk.Box()
        drag_listener = Gtk.EventBox()
        drag_listener.add(self.prompt)

        self.prompt_input = Gtk.Entry(
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

        self.prompt.pack_start(self.prompt_input, True, True, 0)
        self.prompt.pack_end(self.prefs_btn, False, False, 0)

        self.results_view = ResultsView(self.settings, self.apply_css)

        self.theme_root.pack_start(drag_listener, False, True, 0)
        self.theme_root.pack_start(self.results_view, False, True, 0)

        self.frame.show_all()

        self.connect("focus-in-event", lambda *_: self.on_focus_in())
        self.connect("focus-out-event", lambda *_: self.on_focus_out())
        drag_listener.connect("button-press-event", self.on_mouse_down)
        self.connect("button-release-event", lambda *_: self.on_mouse_up())
        self.prompt_input.connect("changed", lambda *_: self.on_input_changed())
        self.prompt_input.connect("key-press-event", self.on_input_key_press)
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

        self.theme_root.get_style_context().add_class("app")
        self.prompt_input.get_style_context().add_class("input")
        self.prefs_btn.get_style_context().add_class("prefs-btn")
        prefs_icon_surface = load_icon_surface(f"{paths.ASSETS}/icons/gear.svg", 16, self.get_scale_factor())
        self.prefs_btn.set_image(Gtk.Image.new_from_surface(prefs_icon_surface))

        self.apply_theme()
        self.position_window()
        self.set_opacity(1)

    def deferred_init(self) -> None:
        if self.query_str:
            # select all text in the input field.
            # used when user turns off "start with blank query" setting
            self.prompt_input.select_region(0, -1)
        self.apply_styling()
        events.emit("app:window_ready")

    ######################################
    # GTK Signal Handlers
    ######################################

    def on_initial_draw(self, *_: tuple[Any]) -> None:
        # ULAUNCHER_PERF_START_BOOTTIME is a perf-test probe (see `make perf` in makefile).
        # When set, report elapsed time from the caller's externally-captured /proc/uptime and
        # exit before deferred_init - this is the earliest point at which keyboard input registers.
        if t0 := os.environ.get("ULAUNCHER_PERF_START_BOOTTIME"):
            elapsed_ms = (time.clock_gettime(time.CLOCK_BOOTTIME) - float(t0)) * 1000
            sys.stdout.write(f"ULAUNCHER_PERF first_draw_ms={elapsed_ms:.2f}\n")
            sys.stdout.flush()
            if app := self.get_application():
                app.quit()
            return
        logger.info("Window shown")
        self.disconnect_by_func(self.on_initial_draw)
        scheduling.run_when_idle(self.deferred_init)

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
        events.emit("app:query_changed", self.prompt_input.get_text())

    def activate_result(self, alt: bool) -> None:
        """
        Activate the selected result
        """
        if result := self.results_view.get_active_result():
            events.emit("app:activate_result", result, alt)

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
            and self.get_app().handle_backspace(self.query_str)
        ):
            return True

        if self.results_view.has_results:
            if keyname in ("Up", "ISO_Left_Tab") or (ctrl and keyname == up_alias):
                self.results_view.go_up()
                return True

            if keyname in ("Down", "Tab") or (ctrl and keyname == down_alias):
                self.results_view.go_down()
                return True

            if ctrl and keyname == left_alias:
                entry_widget.set_position(max(0, entry_widget.get_position() - 1))
                return True

            if ctrl and keyname == right_alias:
                entry_widget.set_position(entry_widget.get_position() + 1)
                return True

            if keyname in ("Return", "KP_Enter"):
                self.activate_result(alt)
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

    def get_app(self) -> UlauncherApp:
        return cast("UlauncherApp", self.get_application())

    @property
    def query_str(self) -> str:
        return self.get_app().query

    def apply_css(self, widget: Gtk.Widget) -> None:
        if not self._css_provider:
            self._css_provider = Gtk.CssProvider()
        Gtk.StyleContext.add_provider(
            widget.get_style_context(), self._css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )
        if isinstance(widget, Gtk.Container):
            widget.forall(self.apply_css)

    def _get_shadow_size(self) -> int:
        if not self.is_composited():
            return 0

        return self.settings.window_shadow

    def apply_theme(self) -> None:
        if not self._css_provider:
            self._css_provider = Gtk.CssProvider()
        # Load theme CSS and apply shadow
        theme_css = Theme.load(self.settings.theme_name).get_css(self._get_shadow_size())
        self._css_provider.load_from_data(theme_css.encode())
        self.apply_css(self)
        logger.info('Applying theme "%s"', self.settings.theme_name)
        visual = self.get_screen().get_rgba_visual()
        if visual:
            self.set_visual(visual)

    def get_monitor_size(self) -> Gdk.Rectangle | None:
        if monitor := get_monitor(self.settings.render_on_screen != "default-monitor"):
            return monitor.get_geometry()
        return None

    def position_window(self) -> None:
        if monitor_size := self.get_monitor_size():
            window_width = self.settings.base_width
            pos_x = (monitor_size.width - window_width) / 2
            pos_y = monitor_size.height * 0.1

            prompt_height = self.prompt.get_allocated_height()
            max_height = monitor_size.height - prompt_height - pos_y * 2
            self.results_view.set_max_height(int(max_height))

            # Part II of the Gnome Wayland fix (see above in __init__)
            # Use margins to center the visible content within the full-screen window
            if DESKTOP_ID == "GNOME" and not IS_X11_COMPATIBLE:
                self.frame.set_properties(
                    margin_top=pos_y,
                    margin_bottom=pos_y,
                    margin_start=pos_x,
                    margin_end=pos_x,
                )

            elif self.layer_shell_enabled:
                layer_shell.set_vertical_position(self, pos_y)
            else:
                self.move(int(pos_x + monitor_size.x), int(pos_y + monitor_size.y))

    def close(self, save_query: bool = False) -> None:
        logger.info("Closing Ulauncher window")
        if not save_query or not self.settings.auto_resume:
            events.emit("app:set_query", "", update_input=False)
        if self.settings.grab_mouse_pointer:
            self.toggle_grab_pointer_device(False)
        super().close()
        self.destroy()

    def select_result(self, index: int) -> None:
        self.results_view.select(index)

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

    def set_input(self, query_str: str) -> None:
        self.prompt_input.set_text(query_str)
        self.prompt_input.set_position(-1)

    def show_results(self, update: ResultsUpdate) -> None:
        self.results_view.render(update)
