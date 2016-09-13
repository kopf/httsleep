import httpretty
import mock

from httsleep import HttSleeper

URL = 'http://example.com'


@httpretty.activate
def test_wrapper():
    """Should create a HttSleeper and return its run() return value"""
    httpretty.register_uri(httpretty.GET, URL, body='<html></html>', status=200)
    with mock.patch('httsleep.main.sleep') as mock_sleep:
        httsleep = HttSleeper(URL, {'status_code': 200})
        resp = httsleep.run()
        assert resp.status_code == 200
        assert not mock_sleep.called
