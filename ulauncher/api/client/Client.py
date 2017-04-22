import os
import sys
import pickle
import logging
import traceback
import websocket
from threading import Timer

from ulauncher.api.shared.event import SystemExitEvent

logger = logging.getLogger(__name__)


class Client(object):

    def __init__(self, extension, ws_api_url=os.environ.get('ULAUNCHER_WS_API')):
        self.ws_api_url = ws_api_url
        if not self.ws_api_url:
            raise Exception('ULAUNCHER_WS_API was not specified')

        self.extension = extension
        self.ws = None

    def connect(self):
        websocket.enableTrace(False)
        self.ws = websocket.WebSocketApp(self.ws_api_url,
                                         on_message=self.on_message,
                                         on_error=self.on_error,
                                         on_open=self.on_open,
                                         on_close=self.on_close)
        self.ws.run_forever()

    def on_message(self, ws, message):
        event = pickle.loads(message)
        logger.debug('Incoming event %s' % type(event).__name__)
        try:
            self.extension.trigger_event(event)
        except Exception as e:
            traceback.print_exc(file=sys.stderr)

    def on_error(self, ws, error):
        logger.error('WS Client error %s' % error)

    def on_close(self, ws):
        logger.warning("Connection closed. Exiting")
        self.extension.trigger_event(SystemExitEvent())
        # extension has 0.5 sec to save it's state, after that it will be terminated
        Timer(0.5, os._exit, args=[0]).start()

    def on_open(self, ws):
        self.ws = ws

    def send(self, response):
        logger.debug('Send message')
        self.ws.send(pickle.dumps(response))
