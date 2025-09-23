from __future__ import annotations  # noqa: N999

import json
import logging
import os
import threading
from functools import partial
from typing import Any, Iterator, TextIO

import ulauncher.api

logger = logging.getLogger()


class Client:
    extension: ulauncher.api.Extension
    input_stream: TextIO
    output_stream: TextIO
    """
    Communication layers:
    → Extension subclass
    • This class
    → (OS) input/output streams
    → (Ulauncher process) ExtensionRuntime
    → EventBus
    → the rest of Ulauncher
    """

    def __init__(self, extension: ulauncher.api.Extension, input_stream: TextIO, output_stream: TextIO) -> None:
        self.input_stream = input_stream
        self.output_stream = output_stream
        self.extension = extension

    def read_messages(self) -> Iterator[dict[str, Any]]:
        """Generator that yields messages from input stream."""
        try:
            for raw_line in self.input_stream:
                line = raw_line.strip()
                if line:
                    try:
                        obj = json.loads(line)
                        yield obj
                    except json.JSONDecodeError:
                        logger.warning("Invalid JSON from Ulauncher app %s:", line)
                        continue
        except (EOFError, KeyboardInterrupt):
            # Input stream closed or interrupted
            self.graceful_unload()
            return

    def connect(self) -> None:
        """
        Connects to the extension server and blocks thread
        """
        for message in self.read_messages():
            self.on_message(message)

    def on_message(self, event: dict[str, Any]) -> None:
        """
        Parses message from Ulauncher and triggers extension event
        """
        logger.debug("Incoming event: %s", event)
        self.extension.trigger_event(event)

    def graceful_unload(self, status_code: int = 0) -> None:
        # extension has 0.5 sec to save it's state, after that it will be terminated
        self.extension.trigger_event({"type": "event:unload"})
        threading.Timer(0.5, partial(os._exit, status_code)).start()

    def send(self, response: Any) -> None:
        """Send a JSON object as a newline-delimited message."""
        logger.debug('Send message with keys "%s"', set(response))
        json_str = json.dumps(response)
        self.output_stream.write(json_str + "\n")
        self.output_stream.flush()
