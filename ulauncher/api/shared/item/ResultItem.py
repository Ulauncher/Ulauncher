from ulauncher.util.text_highlighter import highlight_text


class ResultItem(object):

    ICON_SIZE = 40
    UI_FILE = 'result_item'

    score = None  # used by SortedResultList class to maintain sorted by score order of items

    _name = None
    _description = None
    _keyword = None
    _icon = None
    _include_in_results = True
    _selected_by_default = False
    _on_enter = None
    _on_alt_enter = None
    _highlightable = True
    _is_extension = False

    def __init__(self,
                 name=None,
                 description=None,
                 keyword=None,
                 icon=None,
                 include_in_results=True,
                 selected_by_default=False,
                 highlightable=True,
                 on_enter=None,
                 on_alt_enter=None):
        self._name = name
        self._description = description
        self._keyword = keyword
        self._icon = icon
        self._include_in_results = include_in_results
        self._selected_by_default = selected_by_default
        self._on_enter = on_enter
        self._on_alt_enter = on_alt_enter
        self._highlightable = highlightable

    def get_keyword(self):
        """
        If keyword is defined, search will be performed by keyword, otherwise by name.
        """
        return self._keyword

    def get_name(self):
        return self._name

    def get_search_name(self):
        """
        Returns string that will be used for search
        :rtype: str
        """
        return self.get_name()

    def get_name_highlighted(self, query, color):
        """
        :param ~ulauncher.search.Query.Query query:
        :param str color:
        :rtype: str
        """
        if query and self._highlightable:
            return highlight_text(query if not self._is_extension else query.get_argument(''),
                                  self.get_name(),
                                  open_tag='<span foreground="%s">' % color,
                                  close_tag='</span>')
        else:
            # don't highlight if query is empty
            return self.get_name()

    def get_description(self, query):
        """
        optional

        :param ~ulauncher.search.Query.Query query:
        """
        return self._description

    def get_icon(self):
        """
        optional

        :rtype: :class:`Gtk.PixBuf`
        """
        return self._icon

    def include_in_results(self):
        """
        Return True to display item among apps in the default search
        """
        return self._include_in_results

    def selected_by_default(self, query):
        """
        Return True if item should be selected by default
        """
        return self._selected_by_default

    def on_enter(self, query):
        """
        :param ~ulauncher.search.Query.Query query: it is passed only if :meth:`get_keyword` is implemented.
                                                    This allows you to create flows with a result item
        :rtype: :class:`~ulauncher.api.shared.action.BaseAction.BaseAction`
        """
        if callable(self._on_enter):
            return self._on_enter(query)

    def on_alt_enter(self, query):
        """
        Optional alternative enter

        :param ~ulauncher.search.Query.Query query: it is passed only if :meth:`get_keyword` is implemented.
                                                    This allows you to create flows with a result item
        :rtype: :class:`~ulauncher.api.shared.action.BaseAction.BaseAction`
        """
        if callable(self._on_alt_enter):
            return self._on_alt_enter(query)
