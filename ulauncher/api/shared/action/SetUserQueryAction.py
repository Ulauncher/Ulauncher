from ulauncher.api._deprecation import warn_legacy_api  # noqa: N999
from ulauncher.internals import effects

__all__ = ["SetUserQueryAction"]


def SetUserQueryAction(query: str) -> effects.SetQuery:  # noqa: N802
    warn_legacy_api("SetUserQueryAction", "Use `ulauncher.api.effects.set_query(query)` instead.")
    return effects.set_query(query)
