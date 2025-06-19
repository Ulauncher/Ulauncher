from __future__ import annotations

import logging
from typing import Any, Generic, TypedDict, TypeVar

logger = logging.getLogger()


T = TypeVar("T")


class Action(TypedDict, Generic[T], total=False):
    """
    Type annotations for actions.
    """

    type: str  # Type of the action, e.g., "run_command", "open_url"
    data: T  # Extension-defined data that will be passed back to the extension


def copy(text: str) -> Action[str]:
    """
    Creates an action to copy text to the clipboard.
    """
    if not text:
        msg = "Copy argument cannot be empty"
        logger.error(msg)
        raise ValueError(msg)
    if type(text) is not str:
        msg = f'Copy argument "{text}" is invalid. It must be a string'
        logger.error(msg)
        raise TypeError(msg)
    return {"type": "action:clipboard_store", "data": text}


def open(item: str) -> Action[str]:  # noqa: A001
    """
    Creates an action that uses xdg-open to open a file or URL in the default application.
    """
    if not item:
        msg = "Open argument cannot be empty"
        logger.error(msg)
        raise ValueError(msg)
    if type(item) is not str:
        msg = f'Open argument "{item}" is invalid. It must be a string'
        logger.error(msg)
        raise TypeError(msg)
    return {"type": "action:open", "data": item}


def run_script(script: str, args: str = "") -> Action[list[str]]:
    """
    DEPRECATED: use `actions.custom()` and then `subprocess.run()` to run a script from the extension code.

    Creates an action to run a script with optional arguments.
    """
    if not script:
        msg = "Script argument cannot be empty"
        logger.error(msg)
        raise ValueError(msg)
    if type(script) is not str:
        msg = f'Script argument "{script}" is invalid. It must be a string'
        logger.error(msg)
        raise TypeError(msg)
    return {"type": "action:legacy_run_script", "data": [script, args]}


def action_list(actions: list[Any]) -> Action[list[Any]]:
    """
    DEPRECATED: use `actions.custom()` to receive an event in the extension code
                and then run multiple actions in sequence from there.

    Creates an action that runs multiple actions in sequence.
    """
    return {"type": "action:legacy_run_many", "data": actions}


def set_query(query: str) -> Action[str]:
    """
    Replaces the current user query with a new one.
    """
    if not query:
        msg = "Query argument cannot be empty"
        logger.error(msg)
        raise ValueError(msg)
    if type(query) is not str:
        msg = f'Query argument "{query}" is invalid. It must be a string'
        logger.error(msg)
        raise TypeError(msg)
    return {"type": "action:set_query", "data": query}


# This holds references to custom data for use with ExtensionCustomAction
# This way the data never travels to the Ulauncher app and back. Only a reference to it.
# So the data can be anything, even if the serialization doesn't handle it
custom_data_store: dict[int, Any] = {}


def custom(data: Any, keep_app_open: bool = False) -> Action[dict[str, Any]]:
    """
    Creates a custom action to pass data back to the extension when the result item is activated.
    """
    ref = id(data)
    custom_data_store[ref] = data
    replace_data = {"ref": ref, "keep_app_open": keep_app_open}

    return {"type": "action:activate_custom", "data": replace_data}
