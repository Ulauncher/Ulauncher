from __future__ import annotations

from typing import TYPE_CHECKING, Iterable, cast

from ulauncher.api._logging import get_extension_logger
from ulauncher.internals import effect_utils, effects

if TYPE_CHECKING:
    from ulauncher.internals.result import Result

_logger = get_extension_logger()


def convert_to_effect_message(input_data: effects.EffectMessageInput | bool | str | None) -> effects.EffectMessage:
    """Normalize input format that supports boolean and string to represent effects and iterable lists for results"""
    if input_data is None:
        return effects.close_window()

    if isinstance(input_data, bool):
        substitute = effects.do_nothing if input_data else effects.close_window
        _logger.warning(
            "Returning %r from extension handlers is deprecated. Use effects.%s() instead.",
            input_data,
            substitute.__name__,
        )
        return substitute()

    if isinstance(input_data, str):
        _logger.warning(
            "Returning a string from extension handlers is deprecated. Use effects.set_query(<query>) instead."
        )
        return effects.set_query(input_data)

    if isinstance(input_data, dict):
        if effect_utils.is_effect_message(input_data):
            return input_data
        err_msg = f"Invalid effect message dict: {input_data}"
        raise ValueError(err_msg)

    return effects.render_results(list(cast("Iterable[Result]", input_data)))  # collect/flatten iterators to lists
