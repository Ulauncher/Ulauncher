from __future__ import annotations

import asyncio
import html
import logging
from threading import Thread
from typing import Any, Iterator, Literal, cast

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
    active_ext_id: str | None = None

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
        ext: ExtensionController | None = None
        if query.keyword:
            ext = ExtensionController.get_from_keyword(query.keyword)

        if not ext:
            msg = f"Extension could not handle query {query}"
            raise RuntimeError(msg)

        self.active_ext_id = ext.id
        trigger_id = next((t_id for t_id, t in ext.triggers.items() if t.keyword == query.keyword), None)
        event = {
            "type": "event:input_trigger",
            "ext_id": ext.id,
            "args": [query.argument, trigger_id],
        }

        self.send_message(ext.id, event)

    def send_message(self, ext_id: str, message: dict[str, Any]) -> None:
        if ext := ExtensionController.create(ext_id):
            ext.send_message(message)
        else:
            logger.warning("Cannot send message to unknown extension ID %s", ext_id)

    def get_triggers(self) -> Iterator[Result]:
        for ext in ExtensionController.iterate():
            if not ext.is_enabled:
                continue

            for trigger_id, trigger in ext.triggers.items():
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
                self.send_message(ext_id, event_data)

    @events.on
    def trigger_event(self, event: dict[str, Any]) -> None:
        ext_id = cast("str", event.get("ext_id"))
        self.send_message(ext_id, event)

    @events.on
    def handle_response(self, ext_id: str, response: dict[str, Any]) -> None:
        action_metadata = response.get("action")
        if self.active_ext_id != ext_id:
            logger.debug("Ignoring response from inactive extension %s", ext_id)
            return
        if self.active_ext_id and isinstance(action_metadata, list):
            controller = ExtensionController.create(self.active_ext_id)
            for result in action_metadata:
                result["icon"] = controller.get_normalized_icon_path(result.get("icon"))

            results = [Result(**res) for res in action_metadata]
            events.emit("window:show_results", results)
        else:
            events.emit("mode:handle_action", action_metadata)
