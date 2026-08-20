from ulauncher.api.shared.action.SetUserQueryAction import SetUserQueryAction
from ulauncher.api.shared.item.ResultItem import ResultItem
from ulauncher.config import get_data_file
from ulauncher.utils.image_loader import load_image


class CalcCompletionResultItem(ResultItem):

    # pylint: disable=super-init-not-called
    def __init__(self, completion: str, description: str):
        self.completion = completion
        self.description = description

    def get_name(self) -> str:
        return self.completion

    # pylint: disable=arguments-differ
    def get_name_highlighted(self, *args) -> None:
        pass

    def get_description(self, query) -> str:
        return self.description

    def get_icon(self):
        return load_image(get_data_file('media/calculator-icon.png'), self.get_icon_size())

    def on_enter(self, query):
        return SetUserQueryAction(self.completion)
