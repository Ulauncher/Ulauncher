from urllib.parse import quote
import mock
import pytest
from ulauncher.utils.Router import Router, RoutePathEmpty, RouteNotFound, get_url_params


def test_get_url_params():
    p = get_url_params('settings://get/all/?k1=v1&k2=&k3=%s' % quote('!(*#&^%?'))
    assert p['scheme'] == 'settings'
    assert p['path'] == 'get/all/'
    assert p['query'] == {
        'k1': 'v1',
        'k2': '',
        'k3': '!(*#&^%?'
    }

    p = get_url_params('settings://get/all/?')
    assert p['scheme'] == 'settings'
    assert p['path'] == 'get/all/'
    assert p['query'] is None


class TestRouter:

    @pytest.fixture
    def router(self):
        return Router()

    def test_router_route_raises(self, router):
        with pytest.raises(RoutePathEmpty):
            router.route('')

    def test_router_dispatch_raises(self, router):
        with pytest.raises(RouteNotFound):
            router.dispatch(None, 'settings://unknown/path')

    def test_router_dispatch(self, router):
        m = mock.Mock()
        ctx = mock.Mock()

        # pylint: disable=unused-variable
        @router.route('/get/all')
        def get_all(ctx, url_params):
            m(ctx, url_params)
            return 'result'

        assert router.dispatch(ctx, 'settings://get/all?q=1&s=3') == 'result'
        m.assert_called_with(ctx, {
            'scheme': 'settings',
            'path': 'get/all',
            'query': {
                'q': '1',
                's': '3'
            }
        })
