import requests
import pytest

from httsleep.main import HttSleep


URL = 'http://example.com'
REQUEST = requests.Request(method='GET', url=URL)
CONDITION = {'status_code': 200}


def test_request_built_from_url():
    obj = HttSleep(URL, CONDITION)
    assert obj.request.url == URL
    assert obj.request.method == 'GET'


def test_url_or_request():
    """Should raise a ValueError when the url_or_request obj is not a string or request"""
    HttSleep(URL, CONDITION)
    HttSleep(REQUEST, CONDITION)
    with pytest.raises(ValueError):
        HttSleep(123, CONDITION)


def test_ignore_exceptions_default_value():
    obj = HttSleep(URL, CONDITION)
    assert obj.ignore_exceptions == (None,)

    obj = HttSleep(URL, CONDITION, ignore_exceptions=[ValueError, Exception])
    assert obj.ignore_exceptions == (ValueError, Exception)


def test_max_retries_default_value():
    obj = HttSleep(URL, CONDITION, max_retries=123)
    assert obj.max_retries == 123

    with pytest.raises(ValueError):
        obj = HttSleep(URL, CONDITION, max_retries='five')


def test_until():
    obj = HttSleep(URL, CONDITION)
    assert obj.until == [CONDITION]


def test_empty_until():
    with pytest.raises(ValueError):
        obj = HttSleep(URL, {})
    with pytest.raises(ValueError):
        obj = HttSleep(URL, [{}])


def test_invalid_until():
    with pytest.raises(ValueError):
        obj = HttSleep(URL, {'lol': 'invalid'})
    with pytest.raises(ValueError):
        obj = HttSleep(URL, {'status_code': 200, 'lol': 'invalid'})


def test_status_code_cast_as_int():
    obj = HttSleep(URL, {'status_code': '200'})
    assert obj.until[0]['status_code'] == 200


def test_error():
    obj = HttSleep(URL, CONDITION, error={'status_code': 500})
    assert obj.error == [{'status_code': 500}]


def test_invalid_error():
    with pytest.raises(ValueError):
        obj = HttSleep(URL, CONDITION, error={'lol': 'invalid'})
    with pytest.raises(ValueError):
        obj = HttSleep(URL, CONDITION,
                       error={'status_code': 500, 'lol': 'invalid'})


def test_status_code_cast_as_int_in_error():
    obj = HttSleep(URL, CONDITION, error={'status_code': '500'})
    assert obj.error[0]['status_code'] == 500