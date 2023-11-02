from __future__ import annotations

import logging
from typing import Any

from gi.repository import Gdk, Gtk

from ulauncher.api.result import Result
from ulauncher.config import PATHS
from ulauncher.modes.apps.AppResult import AppResult
from ulauncher.modes.extensions.DeferredResultRenderer import DeferredResultRenderer
from ulauncher.modes.extensions.ExtensionServer import ExtensionServer
from ulauncher.modes.ModeHandler import ModeHandler
from ulauncher.modes.shortcuts.run_script import run_script
from ulauncher.ui.ItemNavigation import ItemNavigation
from ulauncher.ui.LayerShell import LayerShellOverlay

# these imports are needed for Gtk to find widget classes
from ulauncher.ui.ResultWidget import ResultWidget  # noqa: F401
from ulauncher.utils.icon import load_icon_surface
from ulauncher.utils.launch_detached import open_detached
from ulauncher.utils.Settings import Settings
from ulauncher.utils.Theme import Theme
from ulauncher.utils.wm import get_monitor

logger = logging.getLogger()


def handle_event(window, event: bool | list | str | dict[str, Any]) -> bool:  # noqa: PLR0912
    if isinstance(event, bool):
        return event
    if isinstance(event, list):
        window.show_results(res if isinstance(res, Result) else Result(**res) for res in event)
        return True
    if isinstance(event, str):
        window.app.query = event
        return True

    event_type = event.get("type", "")
    data = event.get("data")
    extension_id = event.get("ext_id")
    controller = None
    if event_type == "action:open" and data:
        open_detached(data)
    elif event_type == "action:clipboard_store" and data:
        clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
        clipboard.set_text(data, -1)
        clipboard.store()
        window.hide_and_clear_input()
    elif event_type == "action:legacy_run_script" and isinstance(data, list):
        run_script(*data)
    elif event_type == "action:legacy_run_many" and isinstance(data, list):
        keep_open = False
        for action in data:
            if handle_event(window, action):
                keep_open = True
        return keep_open
    elif event_type == "event:activate_custom":
        controller = DeferredResultRenderer.get_instance().get_active_controller()
    elif event_type.startswith("event") and extension_id:
        controller = ExtensionServer.get_instance().get_controller_by_id(extension_id)
    else:
        logger.warning("Invalid result from mode: %s", type(event).__name__)

    if controller:
        controller.trigger_event(event)
        return event.get("keep_app_open", False) if event_type == "event:activate_custom" else True

    return False


class UlauncherWindow(Gtk.ApplicationWindow, LayerShellOverlay):
    _css_provider = None
    results_nav = None
    is_dragging = False
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

        # This box exists only for setting the margin conditionally, based on ^
        # without the theme being able to override it
        self.window_frame = Gtk.Box()
        self.add(self.window_frame)

        window_container = Gtk.Box(app_paintable=True, orientation="vertical")
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
        self.result_box = Gtk.Box(orientation="vertical")
        self.scroll_container.add(self.result_box)

        window_container.pack_start(event_box, True, True, 0)
        window_container.pack_end(self.scroll_container, True, True, 0)

        window_container.get_style_context().add_class("app")
        self.input.get_style_context().add_class("input")
        prefs_btn.get_style_context().add_class("prefs-btn")
        self.result_box.get_style_context().add_class("result-box")

        prefs_icon_surface = load_icon_surface(f"{PATHS.ASSETS}/icons/gear.svg", 16, self.get_scale_factor())
        prefs_btn.set_image(Gtk.Image.new_from_surface(prefs_icon_surface))
        self.window_frame.show_all()

        self.connect("focus-in-event", self.on_focus_in)
        self.connect("focus-out-event", self.on_focus_out)
        event_box.connect("button-press-event", self.on_mouse_down)
        self.connect("button-release-event", self.on_mouse_up)
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
        if not self.is_dragging:
            self.hide()

    def on_focus_in(self, *_args):
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
        self.app._query = self.input.get_text().lstrip()  # noqa: SLF001
        if self.is_visible():
            # input_changed can trigger when hiding window
            self.handle_event(ModeHandler.get_instance().on_query_change(self.app.query))

    def on_input_key_press(self, widget, event) -> bool:  # noqa: PLR0911, PLR0912
        """
        Triggered by user key press
        Return True to stop other handlers from being invoked for the event
        """
        keyname = Gdk.keyval_name(event.keyval)
        alt = bool(event.state & Gdk.ModifierType.MOD1_MASK)
        ctrl = bool(event.state & Gdk.ModifierType.CONTROL_MASK)
        jump_keys = self.settings.get_jump_keys()

        if len(self.settings.arrow_key_aliases) == 4:  # noqa: PLR2004
            left_alias, down_alias, up_alias, right_alias = [*self.settings.arrow_key_aliases]  # type: ignore[misc]
        else:
            left_alias, down_alias, up_alias, right_alias = [None] * 4
            logger.warning(
                "Invalid value for arrow_key_aliases: %s, expected four letters", self.settings.arrow_key_aliases
            )

        if keyname == "Escape":
            self.hide()
            return True

        if ctrl and keyname == "comma":
            self.app.show_preferences()
            return True

        if (
            keyname == "BackSpace"
            and not ctrl
            and not widget.get_selection_bounds()
            and widget.get_position() == len(self.app.query)
        ):
            new_query = ModeHandler.get_instance().on_query_backspace(self.app.query)
            if new_query is not None:
                self.app.query = new_query
                return True

        if self.results_nav:
            if keyname in ("Up", "ISO_Left_Tab") or (ctrl and keyname == up_alias):
                self.results_nav.go_up()
                return True

            if keyname in ("Down", "Tab") or (ctrl and keyname == down_alias):
                self.results_nav.go_down()
                return True

            if ctrl and keyname == left_alias:
                widget.set_position(max(0, widget.get_position() - 1))
                return True

            if ctrl and keyname == right_alias:
                widget.set_position(widget.get_position() + 1)
                return True

            if keyname in ("Return", "KP_Enter"):
                result = self.results_nav.activate(self.app.query, alt=alt)
                self.handle_event(result)
                return True
            if alt and event.string in jump_keys:
                self.select_result(jump_keys.index(event.string))
                return True
        return False

    def on_mouse_down(self, _, event):
        """
        Move the window on drag
        """
        if event.button == 1 and event.type == Gdk.EventType.BUTTON_PRESS:
            self.is_dragging = True
            self.begin_move_drag(event.button, event.x_root, event.y_root, event.time)

    def on_mouse_up(self, *_):
        self.is_dragging = False

    ######################################
    # Helpers
    ######################################

    @property
    def app(self):
        return self.get_application()

    def handle_event(self, event: bool | list | str | dict[str, Any] | None):
        if event is None:
            self.hide_and_clear_input()
            return

        if not handle_event(self, event):
            self.hide_and_clear_input()

    def apply_css(self, widget):
        Gtk.StyleContext.add_provider(
            widget.get_style_context(), self._css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )
        if isinstance(widget, Gtk.Container):
            widget.forall(self.apply_css)

    def apply_theme(self):
        if not self._css_provider:
            self._css_provider = Gtk.CssProvider()
        theme_css = Theme.load(self.settings.theme_name).get_css().encode()
        self._css_provider.load_from_data(theme_css)
        self.apply_css(self)
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

        # Try setting a transparent background
        screen = self.get_screen()
        visual = screen.get_rgba_visual()
        shadow_size = 20 if visual else 0
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

        if self.layer_shell_enabled:
            self.set_vertical_position(pos_y)
        else:
            self.move(pos_x, pos_y)

    def show(self):
        self.present()
        # note: present_with_time is needed on some DEs to defeat focus stealing protection
        # (Gnome 3 forks like Cinnamon or Budgie, but not Gnome 3 itself any longer)
        # The correct time to use is the time of the user interaction requesting the focus, but we don't have access
        # to that, so we use `Gdk.CURRENT_TIME`, which is the same as passing 0.
        self.present_with_time(Gdk.CURRENT_TIME)
        self.position_window()

        if not self.app.query:
            # make sure frequent apps are shown if necessary
            self.show_results([])

        self.input.grab_focus()
        super().show()

    def hide(self, *args, **kwargs):
        """Override the hide method to ensure the pointer grab is released."""
        if self.settings.grab_mouse_pointer:
            self.get_pointer_device().ungrab(0)
        super().hide(*args, **kwargs)
        if self.settings.clear_previous_query:
            self.app.query = ""

    def select_result(self, index):
        self.results_nav.select(index)

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
