import logging
from time import sleep
import warnings

import jsonpath_rw
import requests

from .exceptions import Alarm
from ._compat import string_types


DEFAULT_POLLING_INTERVAL = 2 # in seconds
DEFAULT_MAX_RETRIES = 50
VALID_CONDITIONS = ['status_code', 'json', 'jsonpath', 'text', 'callback']
DEFAULT_SESSION = requests.Session()


class HttSleeper(object):
    """
    :param url_or_request: either a string containing the URL to be polled,
                           or a :class:`requests.Request` object.
    :param until: a list of success conditions, respresented by dicts, or a
                  single success condition dict.
    :param alarms: a list of error conditions, respresented by dicts, or a
                   single error condition dict.
    :param auth: a (username, password) tuple for HTTP authentication.
    :param headers: a dict of HTTP headers.  If specified, these will be merged with (and take
                    precedence over) any headers provided in the session.
    :param session: a Requests session, providing cookie persistence, connection-pooling, and
                    configuration (e.g. headers).
    :param verify: Either a boolean, in which case it controls whether we verify the server's
                   TLS certificate, or a string, in which case it must be a path to a CA
                   bundle to use. If specified, this takes precedence over any value defined
                   in the session (which itself would be ``True``, by default).
    :param polling_interval: how many seconds to sleep between requests.
    :param max_retries: the maximum number of retries to make, after which
                        a StopIteration exception is raised.
    :param ignore_exceptions: a list of exceptions to ignore when polling
                              the endpoint.
    :param loglevel: the loglevel to use. Defaults to `ERROR`.

    ``url_or_request`` must be provided, along with at least one success condition (``until``).

    """
    def __init__(self, url_or_request, until=None, alarms=None,
                 auth=None, headers=None, session=DEFAULT_SESSION, verify=None,
                 polling_interval=DEFAULT_POLLING_INTERVAL,
                 max_retries=DEFAULT_MAX_RETRIES,
                 ignore_exceptions=None,
                 loglevel=logging.ERROR):
        if not until:
            raise ValueError("No success conditions provided!")
        if isinstance(url_or_request, string_types):
            self.request = requests.Request(
                method='GET', url=url_or_request, auth=auth, headers=headers)
        elif isinstance(url_or_request, requests.Request):
            self.request = url_or_request
        else:
            raise ValueError('url_or_request must be a string containing a URL'
                             ' or a requests.Request object')

        if ignore_exceptions:
            self.ignore_exceptions = tuple(ignore_exceptions)
        else:
            self.ignore_exceptions = tuple()

        if max_retries is not None:
            self.max_retries = int(max_retries)
        else:
            self.max_retries = None

        self.kwargs = {}
        if verify is not None:
            self.kwargs['verify'] = verify
        self.until = until
        self.alarms = alarms
        self.polling_interval = int(polling_interval)
        self.session = session
        self.log = logging.getLogger()
        self.log.setLevel(loglevel)

    def _set_conditions(self, attribute, conditions):
        value = []
        if isinstance(conditions, dict):
            conditions = [conditions]
        if conditions:
            for condition in conditions:
                if not condition:
                    # ignore empty dicts
                    continue
                for key in condition:
                    if key not in VALID_CONDITIONS:
                        raise ValueError(
                            'Invalid key "{}" in condition: {}'.format(key, condition))
                if condition.get('status_code'):
                    condition['status_code'] = int(condition['status_code'])
                # TODO: Add validation for jsonpath
                value.append(condition)

        if value == [] and attribute == 'until':
            raise ValueError('No valid success conditions provided')

        setattr(self, '_{}'.format(attribute), value)

    @property
    def alarms(self):
        return self._alarms

    @alarms.setter
    def alarms(self, value):
        return self._set_conditions('alarms', value)

    @property
    def until(self):
        return self._until

    @until.setter
    def until(self, value):
        return self._set_conditions('until', value)

    def run(self):
        """
        Polls the endpoint until either:

        * a success condition in ``self.until`` is reached, in which case a
          :class:`requests.Request` object is returned
        * an error condition in ``self.alarms`` is encountered, in which case an
          :class:`Alarm` exception is raised
        * ``self.max_retries`` is reached, in which case a :class:`StopIteration` exception
          is raised

        :return: :class:`requests.Response` object.
        """
        while True:
            try:
                response = self.session.send(self.session.prepare_request(self.request), **self.kwargs)
                for condition in self.alarms:
                    if self.meets_condition(response, condition):
                        raise Alarm(response, condition)
                if any([self.meets_condition(response, condition) for condition in self.until]):
                    return response
            except self.ignore_exceptions as e:
                self.log.info('Ignoring exception: {}'.format(e))
            if self.max_retries is not None:
                self.max_retries -= 1
                if self.max_retries <= 0:
                    raise StopIteration("Maximum number of retries reached")
            self.log.info('Not ready, waiting {} seconds...'.format(self.polling_interval))
            sleep(self.polling_interval)

    @staticmethod
    def meets_condition(response, condition):
        if condition.get('status_code') and response.status_code != condition['status_code']:
            return False
        if condition.get('json') and response.json() != condition['json']:
            return False
        if condition.get('text') and response.text != condition['text']:
            return False
        if condition.get('jsonpath'):
            for jsonpath in condition['jsonpath']:
                if isinstance(jsonpath['expression'], string_types):
                    expression = jsonpath_rw.parse(jsonpath['expression'])
                else:
                    expression = jsonpath['expression']
                value = jsonpath['value']
                results = expression.find(response.json())
                if not results:
                    return False
                elif len(results) == 1:
                    if results[0].value != value:
                        return False
                else:
                    if [result.value for result in results] != value:
                        return False
        if condition.get('callback'):
            if condition['callback'](response) == True:
                pass
            else:
                return False
        return True


def httsleep(url_or_request, until=None, alarms=None,
             auth=None, headers=None, session=DEFAULT_SESSION, verify=None,
             polling_interval=DEFAULT_POLLING_INTERVAL,
             max_retries=DEFAULT_MAX_RETRIES,
             ignore_exceptions=None,
             loglevel=logging.ERROR):
    """ Convenience wrapper for the :class:`.HttSleeper` class.
    Creates a HttSleeper object and automatically runs it.

    :return: :class:`requests.Response` object.
    """
    return HttSleeper(
        url_or_request, until=until, alarms=alarms,
        auth=auth, headers=headers, session=session, verify=verify,
        polling_interval=polling_interval,
        max_retries=max_retries,
        ignore_exceptions=ignore_exceptions,
        loglevel=loglevel
    ).run()
