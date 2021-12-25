from decimal import Decimal
from ulauncher.api import Result
from ulauncher.api.shared.action.CopyToClipboardAction import CopyToClipboardAction
from ulauncher.api.shared.action.DoNothingAction import DoNothingAction
from ulauncher.config import get_asset


class CalcResult(Result):

    # pylint: disable=super-init-not-called
    def __init__(self, result: Decimal = None, error: str = 'Unknown error'):
        self.result = result
        self.error = error

    def get_name(self) -> str:
        return f'{Decimal(self.result):n}' if self.result is not None else 'Error!'

    # pylint: disable=super-init-not-called, arguments-differ
    def get_name_highlighted(self, *args) -> None:
        pass

    def get_description(self, query) -> str:
        return 'Enter to copy to the clipboard' if self.result else self.error

    def get_icon(self):
        return get_asset('icons/calculator.png')

    def on_enter(self, query):
        if self.result is not None:
            return CopyToClipboardAction(str(self.result))

        return DoNothingAction()
