import mock
import httpretty
import pytest

from httsleep.main import HttSleep, HttSleepError

URL = 'http://example.com'


@httpretty.activate
def test_run_success():
    """Should return response when a success criteria has been reached"""
    httpretty.register_uri(httpretty.GET, URL, body='<html></html>', status=200)
    with mock.patch('httsleep.main.sleep') as mock_sleep:
        httsleep = HttSleep(URL, {'status_code': 200})
        resp = httsleep.run()
        assert resp.status_code == 200
        assert not mock_sleep.called


@httpretty.activate
def test_run_error():
    """Should raise an HttSleepError when a failure criteria has been reached"""
    httpretty.register_uri(httpretty.GET, URL, body='<html></html>', status=400)
    httsleep = HttSleep(URL, {'status_code': 200}, error={'status_code': 400})
    with pytest.raises(HttSleepError):
        httsleep.run()


@httpretty.activate
def test_run_success_error():
    """Make sure failure criteria takes precedence over success criteria (if httsleep is being used incorrectly)"""
    httpretty.register_uri(httpretty.GET, URL, body='', status=200)
    httsleep = HttSleep(URL, {'status_code': 200}, error={'text': ''})
    with pytest.raises(HttSleepError):
        httsleep.run()


@httpretty.activate
def test_run_retries():
    """Should retry until a success condition is reached"""
    responses = [httpretty.Response(body="Internal Server Error", status=500),
                 httpretty.Response(body="Internal Server Error", status=500),
                 httpretty.Response(body="<html></html>", status=200)]
    httpretty.register_uri(httpretty.GET, URL, responses=responses)
    with mock.patch('httsleep.main.sleep') as mock_sleep:
        resp = HttSleep(URL, {'status_code': 200}).run()
        assert mock_sleep.called
        assert mock_sleep.call_count == 2
    assert resp.status_code == 200
    assert resp.text == '<html></html>'


@httpretty.activate
def test_run_max_retries():
    """Should raise an exception when max_retries is reached"""
    responses = [httpretty.Response(body="Internal Server Error", status=500),
                 httpretty.Response(body="Internal Server Error", status=500),
                 httpretty.Response(body="Internal Server Error", status=500)]
    httpretty.register_uri(httpretty.GET, URL, responses=responses)
    with mock.patch('httsleep.main.sleep') as mock_sleep:
        httsleep = HttSleep(URL, {'status_code': 200}, max_retries=2)
        with pytest.raises(StopIteration):
            httsleep.run()