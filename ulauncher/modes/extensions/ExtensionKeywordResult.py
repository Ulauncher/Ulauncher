from ulauncher.api import SearchableResult
from ulauncher.api.shared.action.SetUserQueryAction import SetUserQueryAction


class ExtensionKeywordResult(SearchableResult):
    def on_enter(self, _):
        return SetUserQueryAction(f'{self.keyword} ')
