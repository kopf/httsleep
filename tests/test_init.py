import requests
import pytest

from httsleep.main import HttSleeper, DEFAULT_MAX_RETRIES


URL = 'http://example.com'
REQUEST = requests.Request(method='GET', url=URL)
CONDITION = {'status_code': 200}


def test_request_built_from_url():
    obj = HttSleeper(URL, CONDITION)
    assert obj.request.url == URL
    assert obj.request.method == 'GET'


def test_url_or_request():
    """Should raise a ValueError when the url_or_request obj is not a string or request"""
    HttSleeper(URL, CONDITION)
    HttSleeper(REQUEST, CONDITION)
    with pytest.raises(ValueError):
        HttSleeper(123, CONDITION)


def test_auth():
    auth = ('myuser', 'mypass')
    obj = HttSleeper(URL, CONDITION, auth=auth)
    assert obj.request.auth == auth


def test_headers():
    headers = {'User-Agent': 'httsleep'}
    obj = HttSleeper(URL, CONDITION, headers=headers)
    assert obj.request.headers == headers


def test_ignore_exceptions_default_value():
    obj = HttSleeper(URL, CONDITION)
    assert obj.ignore_exceptions == tuple()

    obj = HttSleeper(URL, CONDITION, ignore_exceptions=[ValueError, Exception])
    assert obj.ignore_exceptions == (ValueError, Exception)


def test_max_retries():
    obj = HttSleeper(URL, CONDITION)
    assert obj.max_retries == DEFAULT_MAX_RETRIES

    obj = HttSleeper(URL, CONDITION, max_retries=123)
    assert obj.max_retries == 123

    obj = HttSleeper(URL, CONDITION, max_retries=None)
    assert obj.max_retries == None

    with pytest.raises(ValueError):
        HttSleeper(URL, CONDITION, max_retries='five')


def test_until():
    obj = HttSleeper(URL, CONDITION)
    assert obj.until == [CONDITION]


def test_empty_until():
    with pytest.raises(ValueError):
        HttSleeper(URL, {})
    with pytest.raises(ValueError):
        HttSleeper(URL, [{}])


def test_invalid_until():
    with pytest.raises(ValueError):
        HttSleeper(URL, {'lol': 'invalid'})
    with pytest.raises(ValueError):
        HttSleeper(URL, {'status_code': 200, 'lol': 'invalid'})


def test_status_code_cast_as_int():
    obj = HttSleeper(URL, {'status_code': '200'})
    assert obj.until[0]['status_code'] == 200


def test_alarms():
    obj = HttSleeper(URL, CONDITION, alarms={'status_code': 500})
    assert obj.alarms == [{'status_code': 500}]
    obj = HttSleeper(URL, CONDITION, alarms=[{'status_code': 500}])
    assert obj.alarms == [{'status_code': 500}]


def test_invalid_alarms():
    with pytest.raises(ValueError):
        HttSleeper(URL, CONDITION, alarms={'lol': 'invalid'})
    with pytest.raises(ValueError):
        HttSleeper(URL, CONDITION, alarms={'status_code': 500, 'lol': 'invalid'})


def test_status_code_cast_as_int_in_alarm():
    obj = HttSleeper(URL, CONDITION, alarms={'status_code': '500'})
    assert obj.alarms[0]['status_code'] == 500


def test_kwarg_condition():
    def myfunc(*args):
        return
    obj = HttSleeper(URL, status_code=200)
    assert obj.until == [{'status_code': 200}]
    obj = HttSleeper(URL, json={'status': 'SUCCESS'})
    assert obj.until == [{'json': {'status': 'SUCCESS'}}]
    obj = HttSleeper(URL, jsonpath={'expression': 'status', 'value': 'SUCCESS'})
    assert obj.until == [{'jsonpath': {'expression': 'status', 'value': 'SUCCESS'}}]
    obj = HttSleeper(URL, text='done')
    assert obj.until == [{'text': 'done'}]
    obj = HttSleeper(URL, callback=myfunc)
    assert obj.until == [{'callback': myfunc}]
    obj = HttSleeper(URL, status_code=200, callback=myfunc, json={'status': 'success'})
    assert obj.until == [{'status_code': 200, 'callback': myfunc, 'json': {'status': 'success'}}]
