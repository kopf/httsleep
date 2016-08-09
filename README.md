# httsleep

httsleep is a powerful polling library for Python.

[![Build Status](https://travis-ci.org/kopf/httsleep.svg?branch=master)](https://travis-ci.org/kopf/httsleep)

## Simple examples

Let's say we're talking to a RESTful API, and we've just created a 'job'. We know
its ID (`1`), so we're able to poll for its current status.

The simplest example of this would be to poll its endpoint until we get a HTTP 200 OK back.
Once successful, `httsleep` will return the response:

```
from httsleep import httsleep

resp = httsleep('http://myendpoint/jobs/1', status_code=200)
```

You can, of course, change the default polling interval (2 seconds) and the default number of retries (50), along
with other http specifics:

```
httsleep('http://myendpoint/jobs/1', status_code=200, polling_interval=5, max_retries=10,
         auth=(username, password), headers={'User-Agent': 'httsleep'})
```

We can also assert what the JSON body of the response should look like, and specify
exceptions we'd like to ignore:

```
from requests.exceptions import ConnectionError
httsleep('http://myendpoint/jobs/1', status_code=200, json={'status': 'SUCCESS'},
         ignore_exceptions=[ConnectionError])
```

By specifying both a `status_code` and `json` kwarg, joined the two "conditionals" with a boolean AND. More on this in the section "Chaining Conditionals" below.

`httsleep` defaults to making a `GET` request. If we have an API that we want to poll using any other kind of request,
we can pass in a `requests.Request` object instead of a url. This should, of course, be used with care.

```
from requests import Request
req = Request(method='POST', url='http://myendpoint/some_resource', data={'some': 'data'})
httsleep(req, json={'status': 'SUCCESS'})
```

## Conditionals

There are five conditionals built in to httsleep:

### `status_code`

Compare the response's status code:

```
httsleep('http://myendpoint/jobs/1', status_code=200)
```

### `text`

Compare the response's text body:

```
httsleep('http://myendpoint/jobs/1', text="OK!")
```

### `json`

Deserialize the response body as JSON and compare:

```
httsleep('http://myendpoint/jobs/1', json={'status': 'SUCCESS'})
```

### `jsonpath`

Execute a JSONPath query and compare the result:

```
httsleep('http://myendpoint/jobs/1', jsonpath=[{'expression': 'status', 'value': 'SUCCESS'}])
```

JSONPath makes it easy to focus on the information we want to compare in the JSON response
and forget about everything else. The server might put things, such as the job creation and finishing
timestamp in the JSON response, which will make comparing using `json=` impossible. This is where JSONPath really shines.

You might notice that the `jsonpath` kwarg value is a list. A response has only one status code, and only one body, but
multiple jsonpaths might evaluate true for the JSON content returned. Therefore, you can string multiple JSONPaths
together in a list. Logically, they will be evaluated with a boolean AND.

In addition, the `expression` value may be a string representing a JSONPath, or a precompiled JSONPath. The following call
is equivalent to the previous example:

```
from jsonpath_rw.jsonpath import Fields
httsleep('http://myendpoint/jobs/1', jsonpath=[{'expression': Fields('status'), 'value': 'SUCCESS'}])
```

Refer to the [jsonpath-rw](http://jsonpath-rw.readthedocs.io/en/latest/) documentation for more.

### `callback`

Execute a callback function on the response. This function should return False if the response does not match.

```
import datetime

def my_callback(response):
    data = response.json()
    last_scheduled_change = datetime.datetime.strptime(
        data['last_scheduled_change'], '%Y-%m-%d %H:%M:%S')
    if last_scheduled_change > datetime.datetime.utcnow():
        return False


httsleep('http://myendpoint/jobs/1', callback=my_callback)
```

## Chaining conditionals

Until now, we've been specifying conditionals by using direct kwargs. This is a nice shorthand, but it's a little restrictive.
There is another way: using the `until` kwarg, which can consist of a dict containing conditionals, or even a list of such dicts.

For example, the following two calls are equivalent:

```
httsleep('http://myendpoint/jobs/1', status_code=200, json={'status': 'SUCCESS'})
httsleep('http://myendpoint/jobs/1', until={'status_code': 200, 'json': {'status': 'SUCCESS'}})
```

The `until` kwarg is placed directly after the `url_or_request` parameter, so we don't always have to specify it explicitly.

We can chain a list of conditionals with boolean OR by using a list:

```
httsleep('http://myendpoint/jobs/1',
         until=[{'json': {'status': 'SUCCESS'}}, {'json': {'status': 'PENDING'}}])
```

This means, "sleep until the json response is `{'status': 'SUCCESS'}` OR `{'status': 'PENDING'}`".

## Error conditionals

What if the job we've created fails? We need to be able to respond appropriately, instead of polling the endpoint for a long time,
waiting for a successful status. To do this, we set an alarm using the `alarms` kwarg. If an error is detected, an Alarm exception is raised:

```
from httsleep.exceptions import Alarm
try:
    httsleep('http://myendpoint/jobs/1', {'status_code': 200, 'json': {'status': 'SUCCESS'}},
             alarms=[{'json': {'status': 'ERROR'}}, {'json': {'status': 'CRITICAL'}}, {'status_code': 500}])
except Alarm as e:
    if e.response.status_code == 500:
        print "There was an internal system error!"
    else:
        print "The job has error'd out with status {}!".format(e.response.json()['status'])
        print "The condition that matched this was {}".format(e.alarm)
```

As shown in this code, the actual response is stored within the exception, along with the alarm condition that matched the response.

## Going crazy

As the last two sections have shown, we can really squeeze a lot of flexibility out of `httsleep`.

We can see how far this can be taken (perhaps too far) in the next example:

```
until = [{'status_code': 200, 'jsonpath': [{'expression': 'status', 'value': 'OK'}]}
alarms = [{'json': {'status': 'ERROR'}},
          {'jsonpath': [{'expression': 'status', 'value': 'UNKNOWN'},
                        {'expression': 'owner', 'value': 'Chris'}],
           'callback': is_job_really_failing},
          {'status_code': 404}]
httsleep('http://myendpoint/jobs/1', until, alarms=alarms)
```

* Poll `http://myendpoint/jobs/1` until
    * it returns a status code of 200
    * AND the `status` key in its response has the value `OK`
* but raise an error if
    * the `status` key has the value `ERROR`
    * OR the `status` key has the value `UNKNOWN` AND the `owner` key has the value `Chris` AND the function `is_job_really_dying` doesn't return `False`
    * OR the status code is 404

## TODO

* Finalize API
* Write documentation (this doesn't count)
* Release on pypi
