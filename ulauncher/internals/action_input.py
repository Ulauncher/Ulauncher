from __future__ import annotations

from typing import TYPE_CHECKING, Iterable, Union, cast

from ulauncher.internals import actions

if TYPE_CHECKING:
    from ulauncher.internals.result import Result

# Input format that we will convert to an ActionMessage
ActionMessageInput = Union[actions.ActionMessage, bool, str, Iterable["Result"]]


def convert_to_action_message(input_data: ActionMessageInput | None) -> actions.ActionMessage | list[Result]:
    """Normalize input format that supports iterable lists for results and boolean and string actions"""
    if isinstance(input_data, bool) or input_data is None:
        return actions.do_nothing() if input_data else actions.close_window()
    if isinstance(input_data, str):
        return actions.set_query(input_data)
    if isinstance(input_data, dict):
        if actions.is_valid(input_data):
            return cast("actions.ActionMessage", input_data)  # TypedDict unions can't be narrowed by runtime checks
        err_msg = f"Invalid action message dict: {input_data}"
        raise ValueError(err_msg)
    return list(cast("Iterable[Result]", input_data))  # collect/flatten iterators to lists
