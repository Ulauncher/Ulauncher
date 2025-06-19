from __future__ import annotations  # noqa: N999

from typing import Any

from ulauncher.api.actions import Action, run_script
from ulauncher.api.warnings import deprecation_warning


@deprecation_warning(
    "use `ulauncher.api.actions.custom(data: Any)` and then "
    "handle the `on_item_enter` event using `subprocess.run()` "
    "to run a script from the extension code."
)
def RunScriptAction(*args: Any, **kwargs: Any) -> Action[list[str]]:  # noqa: N802
    """Run run_script() to maintain backward compatibility."""
    return run_script(*args, **kwargs)
