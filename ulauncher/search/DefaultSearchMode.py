from ulauncher.ext.SearchMode import SearchMode
from ulauncher.ext.actions.ActionList import ActionList
from ulauncher.ext.actions.RenderResultListAction import RenderResultListAction
from ulauncher.search.apps.AppDb import AppDb

from ulauncher.search.web.GoogleResultItem import GoogleResultItem
from ulauncher.search.web.WikipediaResultItem import WikipediaResultItem


class DefaultSearchMode(SearchMode):

    def on_query(self, query):
        custom_items = [GoogleResultItem(), WikipediaResultItem()]
        keyword = query.get_keyword()
        action_item = next((i for i in custom_items if i.get_keyword() == keyword), None)

        if action_item:
            result_list = (action_item,)
        else:
            result_list = AppDb.get_instance().find(query)

            if len(result_list):
                # add web search items
                result_list.extend(custom_items)

            if not len(result_list) and query:
                # default search
                map(lambda i: i.set_default_search(True), custom_items)
                result_list = custom_items

        return ActionList((RenderResultListAction(result_list),))
