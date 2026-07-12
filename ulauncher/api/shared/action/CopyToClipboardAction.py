from ulauncher.api._deprecation import warn_legacy_api  # noqa: N999
from ulauncher.internals import effects


def CopyToClipboardAction(text: str) -> effects.LegacyCopy:  # noqa: N802
    warn_legacy_api("CopyToClipboardAction", "Call `self.clipboard_store(text)` on your Extension instead.")
    if not isinstance(text, str):
        msg = f'Copy argument "{text}" is invalid. It must be a string'
        raise TypeError(msg)
    return {"type": effects.EffectType.LEGACY_COPY, "text": text}
