from __future__ import annotations

import contextlib
import json
import logging
import os
from typing import TYPE_CHECKING, cast

if TYPE_CHECKING:
    from ulauncher.internals.effects import SetQuery

_logger = logging.getLogger(__name__)
_triggers: dict[str, dict[str, str]] = {}

with contextlib.suppress(json.JSONDecodeError, TypeError):
    _triggers = json.loads(os.environ.get("EXTENSION_TRIGGERS", "{}"))


def _get_current_keyword(query: str) -> str | None:
    """Extract keyword from current query, if present."""
    if not query or " " not in query:
        return None

    query_keyword = query.split(" ", 1)[0]

    # Check if this is actually a keyword (exists in triggers)
    for trigger_data in _triggers.values():
        if query_keyword == trigger_data.get("keyword"):
            return query_keyword

    return None


def _build_query(argument: str, trigger_id: str) -> str:
    match = _triggers.get(trigger_id)
    if match and (keyword := match.get("keyword")):
        return f"{keyword} {argument}" if argument else keyword
    msg = f"Unknown trigger_id '{trigger_id}'"
    raise ValueError(msg)


def _handle_legacy_query(query: str) -> str | None:
    """
    Detect and substitute legacy keyword queries.

    Returns the substituted query or None if no substitution needed.
    """
    parts = query.strip().split(" ", 1)
    if not parts:
        return None

    potential_keyword = parts[0]
    argument = parts[1] if len(parts) > 1 else ""

    # Check if this matches a default trigger keyword
    for trigger_id, trigger_data in _triggers.items():
        default_keyword = trigger_data.get("default_keyword")
        if default_keyword == potential_keyword:
            _logger.warning(
                "Extension is using deprecated set_query('%s'). Please update to use set_query('%s', '%s') instead.",
                query,
                argument,
                trigger_id,
            )
            return _build_query(argument, trigger_id)

    # Doesn't match any default - warn about unknown keyword
    _logger.warning(
        "Extension is using set_query with keyword '%s' that doesn't match any trigger defaults. "
        "This may not work as expected.",
        potential_keyword,
    )

    return None


def transform(current_query: str, effect: SetQuery) -> SetQuery:
    """
    Transform a set_query effect based on trigger_id.

    :param current_query: The current query string (e.g., "kw arg")
    :param effect: The SetQuery effect to transform
    :return: Transformed SetQuery effect with updated data
    """
    trigger_id = cast("str | None", effect.get("ext_trigger_id", ""))
    query = effect["data"]

    # Case 1: Explicit trigger_id provided
    if trigger_id:
        return {"type": "effect:set_query", "data": _build_query(query, trigger_id)}

    # Case 2: trigger_id is None (keep current keyword, replace argument)
    if trigger_id is None:
        current_keyword = _get_current_keyword(current_query)
        if current_keyword:
            full_query = f"{current_keyword} {query}" if query else current_keyword
            return {"type": "effect:set_query", "data": full_query}
        # No current keyword, use query as-is
        _logger.warning(
            "Extension used set_query with trigger_id=None but no current keyword is active. Using query as-is."
        )
        return {"type": "effect:set_query", "data": query}

    # Case 3: No trigger_id provided (empty string) - legacy handling
    # Try to detect if this is a legacy keyword query
    substituted = _handle_legacy_query(query)
    if substituted:
        return {"type": "effect:set_query", "data": substituted}

    # Not a legacy keyword query - warn about future deprecation
    _logger.warning(
        "Extension is using set_query('%s') without trigger_id. "
        "This pattern will be unsupported in the future. "
        "Please use set_query(argument, trigger_id) instead.",
        query,
    )

    return {"type": "effect:set_query", "data": query}
