httsleep
========

|Build Status|

|Coverage Status|

httsleep is a powerful polling library for Python.

Idea
----

Set your success conditions, set a few alarms, and get polling!

::

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
       try:
          response = httsleep(
              'http://myendpoint/jobs/1', until, alarms=alarms,
              max_retries=20)
       except Alarm as e:
           print "Response was:", e.response
           print "Alarm condition that matched was:", e.alarm

Translated into English, this means:

-  Poll ``http://myendpoint/jobs/1`` -- at most 20 times -- until

   -  it returns a status code of ``200``
   -  AND the ``status`` key in its response has the value ``OK``

-  but raise an alarm if

   -  the ``status`` key has the value ``ERROR``
   -  OR the ``status`` key has the value ``UNKNOWN`` AND the ``owner``
      key has the value ``Chris`` AND the function
      ``is_job_really_dying`` returns ``True``
   -  OR the status code is 404

Documentation
-------------

http://httsleep.readthedocs.io/

Installing
----------

::

    pip install httsleep

Testing
-------

::

    pip install -e .
    pip install -r test-requirements.txt
    py.test

.. |Build Status| image:: https://travis-ci.org/kopf/httsleep.svg?branch=master
   :target: https://travis-ci.org/kopf/httsleep
.. |Coverage Status| image:: https://coveralls.io/repos/github/kopf/httsleep/badge.svg?branch=master
   :target: https://coveralls.io/github/kopf/httsleep?branch=master
