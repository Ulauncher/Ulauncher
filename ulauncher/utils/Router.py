from urllib.parse import urlparse, parse_qsl


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
        params = urlparse(url)
        query = dict(parse_qsl(params.query)) if params.query else None
        try:
            callback = self._callbacks[params.path.strip('/')]
        except KeyError as e:
            raise RouteNotFound('Route not found for path %s' % params.path) from e

        return callback(context, query)

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
