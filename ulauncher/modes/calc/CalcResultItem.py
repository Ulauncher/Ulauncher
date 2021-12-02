from ulauncher.api.shared.action.CopyToClipboardAction import CopyToClipboardAction
from ulauncher.api.shared.action.DoNothingAction import DoNothingAction
from ulauncher.api.shared.item.ResultItem import ResultItem
from ulauncher.config import get_data_file
from ulauncher.utils.image_loader import load_image


class CalcResultItem(ResultItem):

    # pylint: disable=super-init-not-called
    def __init__(self, result: str = None, error: str = 'Unknown error'):
        self.result = result
        self.error = error

    def get_name(self) -> str:
        return str(self.result) if self.result is not None else 'Error!'

    # pylint: disable=super-init-not-called, arguments-differ
    def get_name_highlighted(self, *args) -> None:
        pass

    def get_description(self, query) -> str:
        return 'Enter to copy to the clipboard' if self.result else self.error

    def get_icon(self):
        return load_image(get_data_file('icons/calculator.png'), self.get_icon_size())

    def on_enter(self, query):
        if self.result is not None:
            return CopyToClipboardAction(str(self.result))

        return DoNothingAction()
