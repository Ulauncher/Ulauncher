from ulauncher.internals import effects  # noqa: N999


def CopyToClipboardAction(text: str) -> effects.LegacyCopy:  # noqa: N802
    if not isinstance(text, str):
        msg = f'Copy argument "{text}" is invalid. It must be a string'
        raise TypeError(msg)
    return {"type": effects.EffectType.LEGACY_COPY, "data": text}
