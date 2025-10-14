from __future__ import annotations

import asyncio
import html
import logging
from threading import Thread
from typing import Any, Iterator, Literal

from gi.repository import GLib

from ulauncher.internals.query import Query
from ulauncher.internals.result import ActionMetadata, Result
from ulauncher.modes.base_mode import BaseMode
from ulauncher.modes.extensions.extension_controller import ExtensionController
from ulauncher.utils.eventbus import EventBus

DEFAULT_ACTION = True  #  keep window open and do nothing
logger = logging.getLogger()
events = EventBus("extensions")


class ExtensionTrigger(Result):
    searchable = True


class ExtensionMode(BaseMode):
    active_ext: ExtensionController | None = None
    _trigger_cache: dict[str, tuple[str, str]] = {}  # keyword: (trigger_id, ext_id)

    def __init__(self) -> None:
        events.set_self(self)
        GLib.idle_add(self.start_extensions)

    def start_extensions(self) -> None:
        for ext in ExtensionController.iterate():
            if ext.is_enabled and not ext.has_error:
                ext.start_detached()
                # legacy_preferences_load is useless and deprecated
                prefs = {p_id: pref.value for p_id, pref in ext.preferences.items()}
                ext.send_message({"type": "event:legacy_preferences_load", "args": [prefs]})

    def handle_query(self, query: Query) -> None:
        if not query.keyword:
            msg = f"Extensions currently only support queries with a keyword ('{query}' given)"
            raise RuntimeError(msg)

        if trigger_cache_entry := self._trigger_cache.get(query.keyword, None):
            trigger_id, ext_id = trigger_cache_entry
            ext = ExtensionController.create(ext_id)
            self.active_ext = ext
            event = {
                "type": "event:input_trigger",
                "ext_id": ext.id,
                "args": [query.argument, trigger_id],
            }

            ext.send_message(event)
            return

        msg = f"Extension could not handle query {query}"
        raise RuntimeError(msg)

    def get_triggers(self) -> Iterator[Result]:
        self._trigger_cache.clear()
        for ext in ExtensionController.iterate():
            if not ext.is_enabled or ext.has_error:
                continue

            for trigger_id, trigger in ext.triggers.items():
                self._trigger_cache[trigger.keyword] = (trigger_id, ext.id)

                action = (
                    f"{trigger.keyword} "
                    if trigger.keyword
                    else {
                        "type": "action:launch_trigger",
                        "args": [trigger_id],
                        "ext_id": ext.id,
                    }
                )

                yield ExtensionTrigger(
                    name=html.escape(trigger.name),
                    description=html.escape(trigger.description),
                    icon=ext.get_normalized_icon_path(trigger.icon),
                    keyword=trigger.keyword,
                    on_enter=action,
                )

    def activate_result(self, result: Result, query: Query, alt: bool) -> ActionMetadata:
        """
        Called when a result is activated.
        Override this method to handle the activation of a result.
        """
        handler = getattr(result, "on_alt_enter" if alt else "on_enter", DEFAULT_ACTION)
        return handler(query) if callable(handler) else handler

    def run_ext_batch_job(
        self, extension_ids: list[str], jobs: list[Literal["start", "stop"]], done_msg: str | None = None
    ) -> None:
        ext_controllers = [ExtensionController.create(ext_id) for ext_id in extension_ids]

        # run the reload in a separate thread to avoid blocking the main thread
        async def run_batch_async() -> None:
            for job in jobs:
                if job == "start":
                    await asyncio.gather(*[c.start() for c in ext_controllers if c.is_enabled])
                elif job == "stop":
                    await asyncio.gather(*[c.stop() for c in ext_controllers])

        def run_batch() -> None:
            asyncio.run(run_batch_async())

        Thread(target=run_batch).start()

        logger.info(done_msg)

    @events.on
    def reload(
        self,
        extension_ids: list[str] | None = None,
    ) -> None:
        if not extension_ids:
            logger.warning("Reload message received without any extension IDs. No extensions will be restarted.")
            return

        logger.info("Reloading extension(s): %s", ", ".join(extension_ids))

        self.run_ext_batch_job(extension_ids, ["stop", "start"], done_msg=f"{len(extension_ids)} extensions (re)loaded")

    @events.on
    def stop(self, extension_ids: list[str] | None = None) -> None:
        if not extension_ids:
            logger.warning("Stop message received without any extension IDs. No extensions will be stopped.")
            return

        logger.info("Stopping extension(s): %s", ", ".join(extension_ids))

        self.run_ext_batch_job(extension_ids, ["stop"], done_msg=f"{len(extension_ids)} extensions stopped")

    @events.on
    def update_preferences(self, ext_id: str, data: dict[str, Any]) -> None:
        ext = ExtensionController.create(ext_id)
        for p_id, new_value in data.get("preferences", {}).items():
            pref = ext.preferences.get(p_id)
            if pref and new_value != pref.value:
                event_data = {"type": "event:update_preferences", "args": [p_id, new_value, pref.value]}
                ext.send_message(event_data)

    @events.on
    def trigger_event(self, event: dict[str, Any]) -> None:
        if not self.active_ext:
            logger.error("No active extension to send event to")
            return
        self.active_ext.send_message(event)

    @events.on
    def handle_response(self, ext_id: str, response: dict[str, Any]) -> None:
        if not self.active_ext:
            logger.error("No active extension to handle response")
            return
        if self.active_ext.id != ext_id:
            logger.debug("Ignoring response from inactive extension %s", ext_id)
            return

        action_metadata = response.get("action")
        if isinstance(action_metadata, list):
            for result in action_metadata:
                result["icon"] = self.active_ext.get_normalized_icon_path(result.get("icon"))

            results = [Result(**res) for res in action_metadata]
            events.emit("window:show_results", results)
            return
        events.emit("mode:handle_action", action_metadata)
