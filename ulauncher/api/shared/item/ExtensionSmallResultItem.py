from ulauncher.internals.result import Result  # noqa: N999


# TODO: deprecate this class. Use ulauncher.api.Result with compact=True instead
class ExtensionSmallResultItem(Result):
    compact = True
