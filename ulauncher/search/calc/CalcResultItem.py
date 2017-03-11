from ulauncher.config import get_data_file
from ulauncher.helpers import load_image
from ulauncher.result_list.result_item.ResultItem import ResultItem
from ulauncher.result_list.item_action.ActionList import ActionList
from ulauncher.result_list.item_action.CopyToClipboardAction import CopyToClipboardAction


class CalcResultItem(ResultItem):

    def __init__(self, result=None, error=None):
        self.result = result
        self.error = error

    def get_name(self):
        return str(self.result) if self.result is not None else 'Error!'

    def get_name_highlighted(serlf, *args):
        pass

    def get_description(self, query):
        return 'Enter to copy to the clipboard' if self.result else self.error

    def get_icon(self):
        return load_image(get_data_file('media/calculator-icon.png'), self.ICON_SIZE)

    def on_enter(self, query):
        if self.result is not None:
            return ActionList([CopyToClipboardAction(str(self.result))])
        else:
            return ActionList()
