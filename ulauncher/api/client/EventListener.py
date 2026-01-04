from __future__ import annotations  # noqa: N999

from typing import Iterable

import ulauncher.api.extension
import ulauncher.api.shared.event
from ulauncher.internals import actions
from ulauncher.internals.result import Result


class EventListener:
    """
    Base event listener class
    """

    def on_event(
        self, _event: ulauncher.api.shared.event.BaseEvent, _extension: ulauncher.api.extension.Extension
    ) -> actions.ActionMessage | Iterable[Result]:
        """
        :return: Action to run (for KeywordQueryEvent, this should only return Iterable[Result])
        """
        return actions.do_nothing()
