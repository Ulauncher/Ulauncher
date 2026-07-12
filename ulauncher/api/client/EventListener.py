from __future__ import annotations  # noqa: N999

from typing import TYPE_CHECKING

from ulauncher.api._deprecation import warn_legacy_api

if TYPE_CHECKING:
    from ulauncher.api.event import BaseEvent
    from ulauncher.api.extension import Extension
    from ulauncher.internals import effects


class EventListener:
    """
    Base event listener class
    """

    def __init__(self) -> None:
        warn_legacy_api(
            "EventListener", "Define handler methods like `on_input` directly on your `Extension` subclass."
        )

    def on_event(self, _event: BaseEvent, _extension: Extension) -> effects.EffectMessageInput | None:
        """
        :return: Effect to run (for KeywordQueryEvent, this should only return Iterable[Result])
        """
