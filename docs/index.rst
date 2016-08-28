.. httsleep documentation master file, created by
   sphinx-quickstart on Fri Aug 12 11:27:40 2016.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

httsleep
========

A python library for polling HTTP endpoints -- batteries included!

httsleep aims to take care of any situation where you may need to poll a remote
endpoint over HTTP, waiting for a certain response.

Contents
--------

.. toctree::
   :maxdepth: 2

   tutorial
   api_reference


Motivation
----------

Polling a remote endpoint over HTTP (e.g. waiting for a job to complete) is a
very common task. The fact that there are no truly flexible polling libraries
available leads to developers reproducing this boilerplate code time and time
again.

A Simple Example
++++++++++++++++

Maybe you want to just poll until you get a HTTP status code 200?

.. code-block:: python

   resp = httsleep('http://server/endpoint', status_code=200)

This example would be easily replaced with a few lines of Python code.
However, most real-world cases aren't as simple as this, and your
polling code ends up becoming more and more complicated -- dealing with values
in JSON payloads, cases where the remote server is unreachable, or cases where
the job running remotely has errored out and we need to react accordingly.

httsleep aims to cover all of these cases -- and more -- by providing an array of
validators (e.g. ``status_code``, ``json`` and, most powerfully, ``jsonpath``)
which can be chained together logically, removing the burden of having to write
any of this boilerplate code ever again.

A Real-World Example
++++++++++++++++++++

"Poll my endpoint until it responds with the JSON payload ``{'status': 'SUCCESS'}``
and a HTTP status code 200, but raise an alarm if the HTTP status code is 500 or if the
JSON payload is ``{'status': 'TIMEOUT'}``. If a ``ConnectionError`` is thrown, ignore it, and
give up after 20 attempts."

.. code-block:: python

    resp = httsleep('http://server/endpoint',
                    until={'json': {'status': 'SUCCESS'},
                           'status_code': 200},
                    alarms=[{'status_code': 500},
                            {'json': {'status': 'TIMEOUT'}}],
                    ignore_exceptions=[ConnectionError],
                    max_retries=20)


The Python code required to cover this logic would be significantly more complex,
not to mention that it would require an extensive test suite be written.

This is the idea behind httsleep: outsource all of this logic to a library and
not have to reimplement it for each different API you use.



Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

