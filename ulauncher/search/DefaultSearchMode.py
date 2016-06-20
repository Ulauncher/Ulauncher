from ulauncher.ext.SearchMode import SearchMode
from ulauncher.ext.actions.ActionList import ActionList
from ulauncher.ext.actions.RenderResultListAction import RenderResultListAction
from ulauncher.search.apps.AppDb import AppDb

from ulauncher.search.shortcuts.ShortcutsDb import ShortcutsDb


class DefaultSearchMode(SearchMode):

    def on_query(self, query):
        shortcut_items = ShortcutsDb.get_instance().get_result_items()
        action_item = next((i for i in shortcut_items if query.startswith('%s ' % i.get_keyword())), None)

        if action_item:
            # user typed something like "google what is python?"
            # Ulauncher will show one result item. In this case with a shortcut to Google for "what is python?"
            result_list = (action_item,)
        else:
            result_list = AppDb.get_instance().find(query)

            # extend sorted apps with shortcuts, by calculating score and reordering result_list
            result_list.extend(shortcut_items)

            if not len(result_list) and query:
                # default search
                default_items = filter(lambda i: i.is_default_search, shortcut_items)
                map(lambda i: i.activate_default_search(True), shortcut_items)
                result_list = default_items

        return ActionList((RenderResultListAction(result_list),))
