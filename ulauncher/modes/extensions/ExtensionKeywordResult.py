from ulauncher.api import Result
from ulauncher.api.shared.action.SetUserQueryAction import SetUserQueryAction


class ExtensionKeywordResult(Result):
    searchable = True

    def on_enter(self, _):
        return SetUserQueryAction(f'{self.keyword} ')
