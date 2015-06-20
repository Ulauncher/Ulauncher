from ulauncher.ext.SearchMode import SearchMode
from ulauncher.ext.actions.ActionList import ActionList
from ulauncher.ext.actions.RenderResultListAction import RenderResultListAction
from ulauncher.search.apps.AppDb import AppDb

from ulauncher.search.web.GoogleResultItem import GoogleResultItem
from ulauncher.search.web.WikipediaResultItem import WikipediaResultItem
from ulauncher.search.web.StackoverflowResultItem import StackoverflowResultItem


class DefaultSearchMode(SearchMode):

    def on_query(self, query):
        custom_items = [GoogleResultItem(), WikipediaResultItem(), StackoverflowResultItem()]
        default_items = custom_items[:2]
        action_item = next((i for i in custom_items if query.startswith('%s ' % i.get_keyword())), None)

        if action_item:
            result_list = (action_item,)
        else:
            result_list = AppDb.get_instance().find(query)

            # add web search items
            result_list.extend(custom_items)

            if not len(result_list) and query:
                # default search
                map(lambda i: i.set_default_search(True), custom_items)
                result_list = default_items

        return ActionList((RenderResultListAction(result_list),))
