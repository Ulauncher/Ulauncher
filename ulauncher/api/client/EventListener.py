from __future__ import annotations  # noqa: N999

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ulauncher.api.extension import Extension
    from ulauncher.api.shared.event import BaseEvent
    from ulauncher.internals.effect_input import EffectMessageInput


class EventListener:
    """
    Base event listener class
    """

    def on_event(self, _event: BaseEvent, _extension: Extension) -> EffectMessageInput | None:
        """
        :return: Effect to run (for KeywordQueryEvent, this should only return Iterable[Result])
        """
