from __future__ import annotations

from typing import TYPE_CHECKING, Iterable, Union, cast

from ulauncher.internals import actions

if TYPE_CHECKING:
    from ulauncher.internals.result import Result

# Input format that we will convert to an ActionMessage
ActionMessageInput = Union[actions.ActionMessage, bool, str, Iterable["Result"]]


def convert_to_action_message(input_data: ActionMessageInput) -> actions.ActionMessage | list[Result]:
    """Normalize input format that supports iterable lists for results and boolean and string actions"""
    if isinstance(input_data, bool):
        return actions.do_nothing() if input_data else actions.close_window()
    if isinstance(input_data, str):
        return actions.set_query(input_data)
    if isinstance(input_data, dict):
        type_field = input_data.get("type")  # type: ignore[call-overload]
        if not isinstance(type_field, str) or not type_field.startswith("action:"):
            err_msg = f"Invalid action message dict: missing or invalid 'type' field: {input_data}"
            raise ValueError(err_msg)
        return cast("actions.ActionMessage", input_data)  # TypedDict unions can't be narrowed by runtime checks
    return list(cast("Iterable[Result]", input_data))  # collect/flatten iterators to lists
