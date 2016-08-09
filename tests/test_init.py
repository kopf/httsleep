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


def test_auth():
    auth = ('myuser', 'mypass')
    obj = HttSleep(URL, CONDITION, auth=auth)
    assert obj.request.auth == auth


def test_headers():
    headers = {'User-Agent': 'httsleep'}
    obj = HttSleep(URL, CONDITION, headers=headers)
    assert obj.request.headers == headers


def test_ignore_exceptions_default_value():
    obj = HttSleep(URL, CONDITION)
    assert obj.ignore_exceptions == tuple()

    obj = HttSleep(URL, CONDITION, ignore_exceptions=[ValueError, Exception])
    assert obj.ignore_exceptions == (ValueError, Exception)


def test_max_retries_default_value():
    obj = HttSleep(URL, CONDITION, max_retries=123)
    assert obj.max_retries == 123

    with pytest.raises(ValueError):
        HttSleep(URL, CONDITION, max_retries='five')


def test_until():
    obj = HttSleep(URL, CONDITION)
    assert obj.until == [CONDITION]


def test_empty_until():
    with pytest.raises(ValueError):
        HttSleep(URL, {})
    with pytest.raises(ValueError):
        HttSleep(URL, [{}])


def test_invalid_until():
    with pytest.raises(ValueError):
        HttSleep(URL, {'lol': 'invalid'})
    with pytest.raises(ValueError):
        HttSleep(URL, {'status_code': 200, 'lol': 'invalid'})


def test_status_code_cast_as_int():
    obj = HttSleep(URL, {'status_code': '200'})
    assert obj.until[0]['status_code'] == 200


def test_alarms():
    obj = HttSleep(URL, CONDITION, alarms={'status_code': 500})
    assert obj.alarms == [{'status_code': 500}]
    obj = HttSleep(URL, CONDITION, alarms=[{'status_code': 500}])
    assert obj.alarms == [{'status_code': 500}]


def test_invalid_alarms():
    with pytest.raises(ValueError):
        HttSleep(URL, CONDITION, alarms={'lol': 'invalid'})
    with pytest.raises(ValueError):
        HttSleep(URL, CONDITION, alarms={'status_code': 500, 'lol': 'invalid'})


def test_status_code_cast_as_int_in_alarm():
    obj = HttSleep(URL, CONDITION, alarms={'status_code': '500'})
    assert obj.alarms[0]['status_code'] == 500


def test_kwarg_condition():
    def myfunc(*args):
        return
    obj = HttSleep(URL, status_code=200)
    assert obj.until == [{'status_code': 200}]
    obj = HttSleep(URL, json={'status': 'SUCCESS'})
    assert obj.until == [{'json': {'status': 'SUCCESS'}}]
    obj = HttSleep(URL, jsonpath={'expression': 'status', 'value': 'SUCCESS'})
    assert obj.until == [{'jsonpath': {'expression': 'status', 'value': 'SUCCESS'}}]
    obj = HttSleep(URL, text='done')
    assert obj.until == [{'text': 'done'}]
    obj = HttSleep(URL, callback=myfunc)
    assert obj.until == [{'callback': myfunc}]
    obj = HttSleep(URL, status_code=200, callback=myfunc, json={'status': 'success'})
    assert obj.until == [{'status_code': 200, 'callback': myfunc, 'json': {'status': 'success'}}]
