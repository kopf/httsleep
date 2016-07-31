import mock
import responses
import pytest

from httsleep.main import HttSleep, HttSleepError

URL = 'http://example.com'


@pytest.fixture(scope='function')
def mock_sleep():
    return mock.Mock('httsleep.main.sleep')


@responses.activate
def test_run_success(mock_sleep):
    """Should return response when a success criteria has been reached"""
    responses.add(responses.GET, URL, body='<html></html>', status=200)
    httsleep = HttSleep(URL, {'status_code': 200})
    resp = httsleep.run()
    assert resp.status_code == 200
    assert not mock_sleep.called



@responses.activate
def test_run_error():
    """Should raise an HttSleepError when a failure criteria has been reached"""
    responses.add(responses.GET, URL, body='<html></html>', status=400)
    httsleep = HttSleep(URL, {'status_code': 200}, error={'status_code': 400})
    with pytest.raises(HttSleepError):
        resp = httsleep.run()


@responses.activate
def test_run_success_error():
    """Make sure failure criteria takes precedence over success criteria (if httsleep is being used incorrectly)"""
    responses.add(responses.GET, URL, body='', status=200)
    httsleep = HttSleep(URL, {'status_code': 200}, error={'text': ''})
    with pytest.raises(HttSleepError):
        resp = httsleep.run()
