from __future__ import annotations

from typing import TYPE_CHECKING, Iterable, Union, cast

from ulauncher.internals import effects

if TYPE_CHECKING:
    from ulauncher.internals.result import Result

# Input format that we will convert to an EffectMessage
EffectMessageInput = Union[effects.EffectMessage, bool, str, Iterable["Result"]]


def convert_to_effect_message(input_data: EffectMessageInput | None) -> effects.EffectMessage | list[Result]:
    """Normalize input format that supports boolean and string to represent effects and iterable lists for results"""
    if isinstance(input_data, bool) or input_data is None:
        return effects.do_nothing() if input_data else effects.close_window()
    if isinstance(input_data, str):
        return effects.set_query(input_data)
    if isinstance(input_data, dict):
        if effects.is_valid(input_data):
            return cast("effects.EffectMessage", input_data)  # TypedDict unions can't be narrowed by runtime checks
        err_msg = f"Invalid effect message dict: {input_data}"
        raise ValueError(err_msg)
    return list(cast("Iterable[Result]", input_data))  # collect/flatten iterators to lists
