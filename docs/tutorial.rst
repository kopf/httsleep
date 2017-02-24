Tutorial
========

Polling
-------

httsleep polls a HTTP endpoint until it receives a response that matches a
success condition. It returns a :class:`requests.Response` object.

.. code-block:: python

   from httsleep import httsleep
   response = httsleep('http://myendpoint/jobs/1', status_code=200)

In this example, httsleep will fire a HTTP GET request at ``http://myendpoint/jobs/1``
every 2 seconds, retrying a maximum of 50 times, until it gets a response with a
status code of ``200``.

We can change these defaults to poll once a minute, but a maximum of 10 times:

.. code-block:: python

   try:
       response = httsleep('http://myendpoint/jobs/1', status_code=200,
                           max_retries=10, polling_interval=60)
   except StopIteration:
       print "Max retries has been exhausted!"

Similar to the Requests library, we can also set the ``auth`` to a ``(username, password)``
tuple and ``headers`` to a dict of headers if necessary. It is worth noting that these are provided as a
convenience, since many APIs will require some form of authentication and client headers, and that
httsleep doesn't duplicate the Requests library's API wholesale. Instead, you can
pass a :class:`requests.Request` object in place of the URL in more specific cases
(e.g. polling using a POST request):

.. code-block:: python

   from requests import Request
   req = Request('http://myendpoint/jobs/1', method='POST',
                 data={'payload': 'here'})
   response = httsleep(req, status_code=200)

If we're polling a server with a dodgy network connection, we might not want to
break on a :class:`requests.exceptions.ConnectionError`, but instead keep polling:

.. code-block:: python

   from requests.exceptions import ConnectionError
   response = httsleep('http://myendpoint/jobs/1', status_code=200,
                       ignore_exceptions=[ConnectionError])


Conditions
----------

Let's move on to specifying conditions. These are the conditions which,
when met, cause httsleep to stop polling.

There are five conditions built in to httsleep:

* ``status_code``
* ``text``
* ``json``
* ``jsonpath``
* ``callback``

The Basics
~~~~~~~~~~

We've seen that ``status_code`` can be used to poll until a response with a certain
status code is received. ``text`` and ``json`` are similar:

.. code-block:: python

   # Poll until the response body is the string "OK!":
   httsleep('http://myendpoint/jobs/1', text="OK!")
   # Poll until the json-decoded response has a certain value:
   httsleep('http://myendpoint/jobs/1', json={'status': 'OK'})

If a ``json`` condition is specified but no JSON object could be decoded, a ValueError
bubbles up. If needs be, this can be ignored by specifying ``ignore_exceptions``.

JSONPath
~~~~~~~~

.. _jsonpath-rw: http://jsonpath-rw.readthedocs.io/en/latest/
.. _refer to its documentation: http://jsonpath-rw.readthedocs.io/en/latest/

The ``json`` condition is all well and good, but what if we're querying a
resource on a RESTful API? The response may look something like the following:

.. code-block:: json

   {
       "id": 35872,
       "created": "2016-01-01 12:00:00",
       "updated": "2016-02-14 14:25:20",
       "status": "OK"
   }


We won't necessarily know what the entire response (e.g. the object's ID, creation date, update date)
will look like. This is where JSONPath comes into play. JSONPath makes it easy
to focus on the information we want to compare in the JSON response
and forget about everything else.

To assert that the ``status`` key of the JSON response is equal to ``"OK"``,
we can use the following JSONPath query:

.. code-block:: python

   httsleep('http://myendpoint/jobs/1',
            jsonpath=[{'expression': 'status', 'value': 'OK'}])

httsleep uses `jsonpath-rw`_ to evaluate JSONPath expressions.
If you're familiar with this library, you can also use pre-compiled JSONPath expressions:

.. code-block:: python

   from jsonpath_rw.jsonpath import Fields
   httsleep('http://myendpoint/jobs/1',
            jsonpath=[{'expression': Fields('status'), 'value': 'OK'}])

You might notice that the ``jsonpath`` kwarg value is a list. A response has
only one status code, and only one body, but multiple JSONPath expressions might
evaluate true for the JSON content returned. Therefore, you can string multiple JSONPaths
together in a list. Logically, they will be evaluated with a boolean AND.

JSONPath is a highly powerful language, similar to XPath for XML. This section
just skims the surface of what's possible with this language.
To find out more about JSONPath and how to use it to build complex expressions,
please `refer to its documentation`_.

Callbacks
~~~~~~~~~

The last condition to have a look at is ``callback``. This allows you to
use your own function to evaluate the response and is intended for very specific
cases where the other conditions might not be flexible enough.

A callback function should return ``True`` if the response matches. Any other
return value will be interpreted as failure by httsleep, and it will keep polling.

Here is an example of a callback that makes sure the ``last_scheduled_change``
is in the past.

.. code-block:: python

   import datetime

   def ensure_scheduled_change_in_past(response):
       data = response.json()
       last_scheduled_change = datetime.datetime.strptime(
           data['last_scheduled_change'], '%Y-%m-%d %H:%M:%S')
       if last_scheduled_change < datetime.datetime.utcnow():
           return True

   httsleep('http://myendpoint/jobs/1', callback=ensure_scheduled_change_in_past)


Multiple Conditionals
---------------------

It's possible to use multiple conditions simultaneously to assert many different things.
Multiple conditions are joined using a boolean "AND".

For example, the following httsleep call will poll until a response with status code ``200`` AND
an empty dict in the JSON body are received:

.. _multiple-condition-codeblock:
.. code-block:: python

   httsleep('http://myendpoint/jobs/1', status_code=200, json={})

The ``until`` kwarg
~~~~~~~~~~~~~~~~~~~

Until now, we've been specifying conditions by using direct kwargs.
This can be a convenient shorthand for simple cases, but it's a little restrictive.
It is also deprecated and will be removed in a future release.

There is another way: using the ``until`` kwarg.
To demonstrate, :ref:`the previous example <multiple-condition-codeblock>` could be rewritten as:

.. code-block:: python

   httsleep('http://myendpoint/jobs/1',
            until={'status_code': 200, 'json': {}})

One benefit of this is added readability -- the client *sleeps until* a certain
response is received. Another is the ability to chain conditions to form not
just boolean ANDs, but also boolean ORs. More on that later in :ref:`Chaining Conditionals <chaining-conditions>`.

Setting Alarms
--------------

Let's return to a previous example:

.. code-block:: python

   # Poll until the json-decoded response has a certain value:
   httsleep('http://myendpoint/jobs/1', json={'status': 'OK'})

What if the job running on the remote server errors out and gets a status of ``ERROR``?
httsleep would keep polling the endpoint, waiting for a status of ``OK``,
until its ``max_retries`` had been exhausted -- not exactly what we'd like to happen.

This is because no alarms have been set.

Alarms can be set using the ``alarms`` kwarg, just like success conditions can be
set using the ``until`` kwarg. Every time it polls an endpoint, httsleep always
checks whether any alarms are set, and if so, evaluates them. If the response matches
an alarm condition, an :class:`httsleep.exceptions.Alarm` exception is raised. If not,
httsleep goes on and checks the success conditions.

Here is a version of the example above, modified so that it raises an :class:`httsleep.exceptions.Alarm`
if the job status is set to ``ERROR``:

.. code-block:: python

   from httsleep.exceptions import Alarm
   try:
       httsleep('http://myendpoint/jobs/1', json={'status': 'OK'},
                alarms={'json': {'status': 'ERROR'}})
   except Alarm as e:
       print "Got a response with status ERROR!"
       print "Here's the response:", e.response
       print "And here's the alarm went off:", e.alarm

As can be seen here, the response object is stored in the exception, along with
the alarm that was triggered.

Any conditions, or combination thereof, can be used to set alarms.

.. _chaining-conditions:

Chaining Conditionals and Alarms
--------------------------------

We've seen that conditions can be joined together with a boolean "AND" by
packing them into a single dictionary.

There are cases where we might want to join conditions using boolean "OR". In
these cases, we simply use lists:

.. code-block:: python

   httsleep('http://myendpoint/jobs/1',
            until=[{'json': {'status': 'SUCCESS'}},
                   {'json': {'status': 'PENDING'}}])

This means, "sleep until the json response is ``{"status": "SUCCESS"}`` OR ``{"status": "PENDING"}``".

As always, we can use the same technique for alarms:

.. code-block:: python

   httsleep('http://myendpoint/jobs/1',
            until=[{'json': {'status': 'SUCCESS'}},
                   {'json': {'status': 'PENDING'}}],
            alarms=[{'json': {'status': 'ERROR'}},
                    {'json': {'status': 'TIMEOUT'}}])


Putting it all together
-----------------------

As we've seen in this short tutorial, you can really squeeze a lot of flexibility out of `httsleep`.

We can see how far this can be taken in the next example:

.. code-block:: python

   until = {
       'status_code': 200,
       'jsonpath': [{'expression': 'status', 'value': 'OK'}]
   }
   alarms = [
       {'json': {'status': 'ERROR'}},
       {'jsonpath': [{'expression': 'status', 'value': 'UNKNOWN'},
                     {'expression': 'owner', 'value': 'Chris'}],
       'callback': is_job_really_failing},
       {'status_code': 404}
   ]
   httsleep('http://myendpoint/jobs/1', until=until, alarms=alarms,
            max_retries=20)


Translated into English, this means:

* Poll ``http://myendpoint/jobs/1`` -- at most 20 times -- until
    * it returns a status code of ``200``
    * AND the ``status`` key in its response has the value ``OK``
* but raise an error if
    * the ``status`` key has the value ``ERROR``
    * OR the ``status`` key has the value ``UNKNOWN`` AND the ``owner`` key has the value ``Chris`` AND the function ``is_job_really_dying`` returns ``True``
    * OR the status code is 404
