from __future__ import annotations

from typing import Any

import ulauncher.api.extension
import ulauncher.api.shared.event


class EventListener:
    """
    Base event listener class
    """

    def on_event(
        self, event: ulauncher.api.shared.event.BaseEvent, extension: ulauncher.api.extension.Extension
    ) -> Any:
        """
        :param ~ulauncher.api.shared.event.BaseEvent event: event that listener was subscribed to
        :param ~ulauncher.api.Extension extension:

        :rtype: bool, strict, dict or None
        :return: Action to run
        """
