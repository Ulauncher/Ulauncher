import re
from urllib.parse import unquote

RE_URL = re.compile(r'^(?P<scheme>.*)://(?P<path>[^\?]*)(\?(?P<query>.*))?$', flags=re.IGNORECASE)


def get_url_params(url):
    params = re.search(RE_URL, url)
    query = params.group('query')
    if query:
        pairs = list(map(lambda kv: kv.split('='), query.split('&')))
        query = {k: unquote(v) for k, v in pairs}
    return {
        'scheme': params.group('scheme'),
        'path': params.group('path'),
        'query': query or None
    }


class Router:
    """
    Usage:

    >>> rt = Router()
    >>>
    >>> class App:
    >>>
    >>>     @rt.route('get/user')
    >>>     def get_user(self, url_params):
    >>>         ...
    >>>         return userObject
    >>>
    >>>     def on_request(self, url):
    >>>         result = rt.dispatch(self, url) # will return userObject for /get/user path
    """

    _callbacks = None

    def __init__(self):
        self._callbacks = {}

    def dispatch(self, context, url):
        url_params = get_url_params(url)
        try:
            callback = self._callbacks[url_params['path'].strip('/')]
        except KeyError as e:
            raise RouteNotFound('Route not found for path %s' % url_params['path']) from e

        return callback(context, url_params)

    def route(self, path):
        if not path:
            raise RoutePathEmpty()

        def decorator(callback):
            self._callbacks[path.strip('/')] = callback
            return callback

        return decorator


class RouterError(RuntimeError):
    pass


class RoutePathEmpty(RouterError):
    pass


class RouteNotFound(RouterError):
    pass
