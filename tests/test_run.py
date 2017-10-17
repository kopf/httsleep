import json

import httpretty
from jsonpath_rw.jsonpath import Fields
import mock
import pytest
from requests.exceptions import ConnectionError

from httsleep.main import HttSleeper, Alarm, DEFAULT_POLLING_INTERVAL

URL = 'http://example.com'


@httpretty.activate
def test_run_success():
    """Should return response when a success criteria has been reached"""
    httpretty.register_uri(httpretty.GET, URL, body='<html></html>', status=200)
    with mock.patch('httsleep.main.sleep') as mock_sleep:
        httsleep = HttSleeper(URL, {'status_code': 200})
        resp = httsleep.run()
        assert resp.status_code == 200
        assert not mock_sleep.called


@httpretty.activate
def test_run_success_with_verify():
    """Should return response when a success criteria has been reached"""
    httpretty.register_uri(httpretty.GET, URL, body='<html></html>', status=200)
    with mock.patch('httsleep.main.sleep') as mock_sleep:
        httsleep = HttSleeper(URL, {'status_code': 200}, verify=False)
        resp = httsleep.run()
        assert resp.status_code == 200
        assert not mock_sleep.called


@httpretty.activate
def test_run_alarm():
    """Should raise an Alarm when a failure criteria has been reached"""
    httpretty.register_uri(httpretty.GET, URL, body='<html></html>', status=400)
    httsleep = HttSleeper(URL, {'status_code': 200}, alarms={'status_code': 400})
    with pytest.raises(Alarm):
        httsleep.run()


@httpretty.activate
def test_run_success_alarm():
    """Make sure failure criteria takes precedence over success criteria (if httsleep is being used incorrectly)"""
    httpretty.register_uri(httpretty.GET, URL, body='', status=200)
    httsleep = HttSleeper(URL, {'status_code': 200}, alarms={'text': ''})
    with pytest.raises(Alarm):
        httsleep.run()


@httpretty.activate
def test_run_retries():
    """Should retry until a success condition is reached"""
    responses = [httpretty.Response(body="Internal Server Error", status=500),
                 httpretty.Response(body="Internal Server Error", status=500),
                 httpretty.Response(body="<html></html>", status=200)]
    httpretty.register_uri(httpretty.GET, URL, responses=responses)
    with mock.patch('httsleep.main.sleep') as mock_sleep:
        resp = HttSleeper(URL, {'status_code': 200}).run()
        assert mock_sleep.called
        assert mock_sleep.call_count == 2
    assert resp.status_code == 200
    assert resp.text == '<html></html>'


@httpretty.activate
def test_run_sleep_default_interval():
    responses = [httpretty.Response(body="Internal Server Error", status=500),
                 httpretty.Response(body="<html></html>", status=200)]
    httpretty.register_uri(httpretty.GET, URL, responses=responses)
    with mock.patch('httsleep.main.sleep') as mock_sleep:
        resp = HttSleeper(URL, {'status_code': 200}).run()
        assert mock_sleep.called_once_with(DEFAULT_POLLING_INTERVAL)


@httpretty.activate
def test_run_sleep_custom_interval():
    responses = [httpretty.Response(body="Internal Server Error", status=500),
                 httpretty.Response(body="<html></html>", status=200)]
    httpretty.register_uri(httpretty.GET, URL, responses=responses)
    with mock.patch('httsleep.main.sleep') as mock_sleep:
        resp = HttSleeper(URL, {'status_code': 200}, polling_interval=6).run()
        assert mock_sleep.called_once_with(6)


@httpretty.activate
def test_run_max_retries():
    """Should raise an exception when max_retries is reached"""
    responses = [httpretty.Response(body="Internal Server Error", status=500),
                 httpretty.Response(body="Internal Server Error", status=500),
                 httpretty.Response(body="Internal Server Error", status=500)]
    httpretty.register_uri(httpretty.GET, URL, responses=responses)
    with mock.patch('httsleep.main.sleep'):
        httsleep = HttSleeper(URL, {'status_code': 200}, max_retries=2)
        with pytest.raises(StopIteration):
            httsleep.run()


@httpretty.activate
def test_ignore_exceptions():
    responses = [httpretty.Response(body=ConnectionError),
                 httpretty.Response(body="{}", status=200)]
    httpretty.register_uri(httpretty.GET, URL, responses=responses)
    with mock.patch('httsleep.main.sleep'):
        httsleep = HttSleeper(URL, {'json': {}}, ignore_exceptions=[ConnectionError])
        resp = httsleep.run()
    assert resp.status_code == 200
    assert resp.text == "{}"


@httpretty.activate
def test_json_condition():
    expected = {'my_key': 'my_value'}
    responses = [httpretty.Response(body=json.dumps({'error': 'not found'}), status=404),
                 httpretty.Response(body=json.dumps(expected), status=200)]
    httpretty.register_uri(httpretty.GET, URL, responses=responses)
    with mock.patch('httsleep.main.sleep'):
        httsleep = HttSleeper(URL, {'json': expected})
        resp = httsleep.run()
    assert resp.status_code == 200
    assert resp.json() == expected


@httpretty.activate
def test_text_condition():
    expected = 'you got it!'
    responses = [httpretty.Response(body='not found', status=404),
                 httpretty.Response(body=expected, status=200)]
    httpretty.register_uri(httpretty.GET, URL, responses=responses)
    with mock.patch('httsleep.main.sleep'):
        httsleep = HttSleeper(URL, {'text': expected})
        resp = httsleep.run()
    assert resp.status_code == 200
    assert resp.text == expected


@httpretty.activate
def test_jsonpath_condition():
    payload = {'status': 'SUCCESS'}
    responses = [httpretty.Response(body=json.dumps(payload), status=200)]
    httpretty.register_uri(httpretty.GET, URL, responses=responses)
    with mock.patch('httsleep.main.sleep'):
        httsleep = HttSleeper(URL, {'jsonpath': [{'expression': 'status', 'value': 'SUCCESS'}]})
        resp = httsleep.run()
    assert resp.status_code == 200
    assert resp.json() == payload


@httpretty.activate
def test_precompiled_jsonpath_expression():
    payload = {'status': 'SUCCESS'}
    responses = [httpretty.Response(body=json.dumps(payload), status=200)]
    httpretty.register_uri(httpretty.GET, URL, responses=responses)
    expression = Fields('status')
    with mock.patch('httsleep.main.sleep'):
        httsleep = HttSleeper(URL, {'jsonpath': [{'expression': expression, 'value': 'SUCCESS'}]})
        resp = httsleep.run()
    assert resp.status_code == 200
    assert resp.json() == payload


@httpretty.activate
def test_jsonpath_condition_multiple_values():
    payload = {'foo': [{'bar': 1}, {'bar': 2}]}
    responses = [httpretty.Response(body=json.dumps(payload), status=200)]
    httpretty.register_uri(httpretty.GET, URL, responses=responses)
    with mock.patch('httsleep.main.sleep'):
        httsleep = HttSleeper(URL, {'jsonpath': [{'expression': 'foo[*].bar', 'value': [1, 2]}]})
        resp = httsleep.run()
    assert resp.status_code == 200
    assert resp.json() == payload


@httpretty.activate
def test_jsonpath_condition_multiple_values():
    payload = {'foo': [{'bar': 1}, {'bar': 2}]}
    responses = [httpretty.Response(body=json.dumps(payload), status=200)]
    httpretty.register_uri(httpretty.GET, URL, responses=responses)
    with mock.patch('httsleep.main.sleep'):
        httsleep = HttSleeper(URL, {'jsonpath': [{'expression': 'foo[*].bar', 'value': [1, 2]}]})
        resp = httsleep.run()
    assert resp.status_code == 200
    assert resp.json() == payload


@httpretty.activate
def test_multiple_jsonpath_conditions():
    payload = {'foo': [{'bar': 1}, {'bar': 2}]}
    responses = [httpretty.Response(body=json.dumps(payload), status=200)]
    httpretty.register_uri(httpretty.GET, URL, responses=responses)
    with mock.patch('httsleep.main.sleep'):
        httsleep = HttSleeper(URL, {'jsonpath': [{'expression': 'foo[0].bar', 'value': 1},
                                                 {'expression': 'foo[1].bar', 'value': 2}]})
        resp = httsleep.run()
    assert resp.status_code == 200
    assert resp.json() == payload


@httpretty.activate
def test_callback_condition():
    def my_func(req):
        if 'very very' in req.text:
            return True
        return False
    text = "Some very very long text here with <b>maybe</b> some html too"
    responses = [httpretty.Response(body='not found', status=404),
                 httpretty.Response(body=text, status=200)]
    httpretty.register_uri(httpretty.GET, URL, responses=responses)
    with mock.patch('httsleep.main.sleep'):
        resp = HttSleeper(URL, {'callback': my_func}).run()
    assert resp.status_code == 200
    assert resp.text == text


@httpretty.activate
def test_multiple_success_conditions():
    responses = [httpretty.Response(body='first response', status=200),
                 httpretty.Response(body='second response', status=200),
                 httpretty.Response(body='third response', status=200)]
    httpretty.register_uri(httpretty.GET, URL, responses=responses)
    conditions = [{'text': 'third response', 'status_code': 200},
                  {'text': 'second response', 'status_code': 200}]
    with mock.patch('httsleep.main.sleep'):
        httsleep = HttSleeper(URL, conditions)
        resp = httsleep.run()
    assert resp.status_code == 200
    assert resp.text == 'second response'


@httpretty.activate
def test_multiple_alarms():
    error_msg = {'status': 'ERROR'}
    responses = [httpretty.Response(body=json.dumps(error_msg), status=500),
                 httpretty.Response(body='Internal Server Error', status=500),
                 httpretty.Response(body='success', status=200)]
    httpretty.register_uri(httpretty.GET, URL, responses=responses)
    alarms = [{'text': 'Internal Server Error', 'status_code': 500},
              {'json': error_msg, 'status_code': 500}]
    with mock.patch('httsleep.main.sleep'):
        httsleep = HttSleeper(URL, {'status_code': 200}, alarms=alarms)
        try:
            httsleep.run()
        except Alarm as e:
            assert e.response.status_code == 500
            assert e.response.json() == error_msg
            assert e.alarm == {'json': error_msg, 'status_code': 500}
        else:
            pytest.fail("No exception raised!")
