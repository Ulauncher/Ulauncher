from typing import Any, Callable, Optional

from ulauncher.api.shared.action.BaseAction import BaseAction
from ulauncher.search.Query import Query
from ulauncher.utils.text_highlighter import highlight_text
from ulauncher.utils.display import get_monitor_scale_factor

OnEnterCallback = Optional[Callable[[Query], Optional[BaseAction]]]


# pylint: disable=too-many-instance-attributes
class ResultItem:

    ICON_SIZE = 40
    UI_FILE = 'result_item'

    score = None  # used by SortedResultList class to maintain sorted by score order of items

    _name = None  # type: str
    _description = None  # type: str
    _keyword = None  # type: str
    _icon = None  # type: Any
    _include_in_results = True  # type: bool
    _selected_by_default = False  # type: bool
    _on_enter = None  # type: OnEnterCallback
    _on_alt_enter = None  # type: OnEnterCallback
    _highlightable = True  # type: bool
    _is_extension = False  # type: bool

    # pylint: disable=too-many-arguments
    def __init__(self,
                 name: str = '',
                 description: str = '',
                 keyword: str = '',
                 icon: Any = None,
                 include_in_results: bool = True,
                 selected_by_default: bool = False,
                 highlightable: bool = True,
                 on_enter: OnEnterCallback = None,
                 on_alt_enter: OnEnterCallback = None):
        if not isinstance(name, str):
            raise TypeError('"name" must be of type "str", "%s" given' % type(name).__name__)
        if not isinstance(description, str):
            raise TypeError('"description" must be of type "str", "%s" given' % type(description).__name__)
        if not isinstance(keyword, str):
            raise TypeError('"keyword" must be of type "str", "%s" given' % type(keyword).__name__)
        self._name = name
        self._description = description
        self._keyword = keyword
        self._icon = icon
        self._include_in_results = include_in_results
        self._selected_by_default = selected_by_default
        self._on_enter = on_enter
        self._on_alt_enter = on_alt_enter
        self._highlightable = highlightable

    @classmethod
    def get_icon_size(cls):
        return cls.ICON_SIZE * get_monitor_scale_factor()

    def get_keyword(self) -> str:
        """
        If keyword is defined, search will be performed by keyword, otherwise by name.
        """
        return self._keyword

    def get_name(self) -> str:
        return self._name

    def get_search_name(self) -> str:
        """
        Returns string that will be used for search
        :rtype: str
        """
        return self.get_name()

    def get_name_highlighted(self, query: Query, color: str) -> Optional[str]:
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
        # don't highlight if query is empty
        return self.get_name()

    # pylint: disable=unused-argument
    def get_description(self, query: Query) -> str:
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

    def on_enter(self, query: Query) -> Optional[BaseAction]:
        """
        :param ~ulauncher.search.Query.Query query: it is passed only if :meth:`get_keyword` is implemented.
                                                    This allows you to create flows with a result item
        :rtype: :class:`~ulauncher.api.shared.action.BaseAction.BaseAction`
        """
        return self._on_enter(query) if callable(self._on_enter) else None

    def on_alt_enter(self, query: Query) -> Optional[BaseAction]:
        """
        Optional alternative enter

        :param ~ulauncher.search.Query.Query query: it is passed only if :meth:`get_keyword` is implemented.
                                                    This allows you to create flows with a result item
        :rtype: :class:`~ulauncher.api.shared.action.BaseAction.BaseAction`
        """
        return self._on_alt_enter(query) if callable(self._on_alt_enter) else None
