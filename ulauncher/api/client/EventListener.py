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
        :return: Action to run
        """
