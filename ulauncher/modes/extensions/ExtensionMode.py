import html
import logging
from typing import Dict
from ulauncher.config import EXTENSIONS_DIR
from ulauncher.modes.BaseMode import BaseMode
from ulauncher.modes.extensions.DeferredResultRenderer import DeferredResultRenderer
from ulauncher.modes.extensions.ExtensionServer import ExtensionServer
from ulauncher.modes.extensions.ExtensionRunner import ExtensionRunner
from ulauncher.modes.extensions.ExtensionKeywordResult import ExtensionKeywordResult
from ulauncher.modes.extensions.ExtensionPreferences import ExtensionPreferences
from ulauncher.modes.extensions.extension_finder import find_extensions
from ulauncher.api.shared.action.DoNothingAction import DoNothingAction

logger = logging.getLogger(__name__)
server = ExtensionServer.get_instance()
server.start()


class ExtensionMode(BaseMode):
    keywords: Dict[str, str] = {}

    def __init__(self):
        self.deferredResultRenderer = DeferredResultRenderer.get_instance()

    def is_enabled(self, query):
        """
        :param ~ulauncher.modes.Query.Query query:
        :rtype: `True` if mode should be enabled for a query
        """
        return query.get_keyword() in self.keywords and " " in query

    def on_query_change(self, query):
        """
        Triggered when user changes a search query

        :param ~ulauncher.modes.Query.Query query:
        """
        self.deferredResultRenderer.on_query_change()

    def handle_query(self, query):
        """
        :param ~ulauncher.modes.Query.Query query:
        :rtype: :class:`~ulauncher.api.shared.action.BaseAction.BaseAction`
        """
        extension_id = self.keywords.get(query.get_keyword())
        controller = server.get_controller(extension_id)
        if controller:
            return controller.handle_query(query)

        # Set the query to show when controller has loaded
        server.queries = {extension_id: query}
        runner = ExtensionRunner.get_instance()
        if not runner.is_running(extension_id):
            runner.run(extension_id)

        return DoNothingAction()

    def get_searchable_items(self):
        """
        :rtype: Iterable[:class:`~ulauncher.api.Result`]
        """
        for ext_id, _ in find_extensions(EXTENSIONS_DIR):
            prefs = ExtensionPreferences.create_instance(ext_id)
            manifest = prefs.manifest
            try:
                manifest.validate()
                manifest.check_compatibility()
                for pref in prefs.get_items():
                    if pref["type"] == 'keyword':
                        self.keywords[pref['value']] = ext_id

                        yield ExtensionKeywordResult(
                            name=html.escape(pref['name']),
                            description=html.escape(pref['description']),
                            keyword=pref['value'],
                            icon=manifest.get_icon_path(path=pref['icon'])
                        )
            # pylint: disable=broad-except
            except Exception as e:
                logger.error('%s: %s', type(e).__name__, e)
