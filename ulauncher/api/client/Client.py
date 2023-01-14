import os
import sys
import pickle
import logging
import traceback
from threading import Timer

import websocket
from ulauncher.api.shared.event import SystemExitEvent

logger = logging.getLogger(__name__)


class Client:
    """
    Instantiated in extension code and manages data transfer from/to Ulauncher app

    :param ~ulauncher.api.client.Extension extension:
    :param str ws_api_url: uses env. var `ULAUNCHER_WS_API` by default
    """

    def __init__(self, extension, ws_api_url=None):
        self.ws_api_url = ws_api_url or os.environ.get('ULAUNCHER_WS_API')
        if not self.ws_api_url:
            raise Exception('ULAUNCHER_WS_API was not specified')

        self.extension = extension
        self.ws = None

    def connect(self):
        """
        Connects to WS server and blocks thread
        """
        websocket.enableTrace(False)
        # pylint: disable=unnecessary-lambda
        self.ws = websocket.WebSocketApp(self.ws_api_url,
                                         on_message=lambda ws, msg: self.on_message(ws, msg),
                                         on_error=lambda ws, error: self.on_error(ws, error),
                                         on_open=lambda ws: self.on_open(ws),
                                         on_close=lambda ws: self.on_close(ws))
        self.ws.run_forever()

    # pylint: disable=unused-argument
    def on_message(self, ws, message):
        """
        Parses message from Ulauncher and triggers extension event

        :param websocket.WebSocketApp ws:
        :param str message:
        """
        event = pickle.loads(message)
        logger.debug('Incoming event %s', type(event).__name__)
        try:
            self.extension.trigger_event(event)
        # pylint: disable=broad-except
        except Exception:
            traceback.print_exc(file=sys.stderr)

    def on_error(self, ws, error):
        logger.error('WS Client error %s', error)

    def on_close(self, ws):
        """
        Terminates extension process on WS disconnect.

        Triggers :class:`~ulauncher.api.shared.event.SystemExitEvent` for graceful shutdown

        :param websocket.WebSocketApp ws:
        """
        logger.warning("Connection closed. Exiting")
        self.extension.trigger_event(SystemExitEvent())
        # extension has 0.5 sec to save it's state, after that it will be terminated
        Timer(0.5, os._exit, args=[0]).start()

    def on_open(self, ws):
        self.ws = ws

    def send(self, response):
        """
        Sends response to Ulauncher

        :param ~ulauncher.api.shared.Response.Response response:
        """
        logger.debug('Send message')
        self.ws.send(pickle.dumps(response))
