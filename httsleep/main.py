import logging
from time import sleep

import requests

from exceptions import HttSleepError


DEFAULT_POLLING_INTERVAL = 2 # in seconds
VALID_CONDITIONS = ['status_code', 'json', 'jsonpath', 'text']


class HttSleep(object):
    def __init__(self, url_or_request, until, error=None,
                 polling_interval=DEFAULT_POLLING_INTERVAL,
                 max_retries=None,
                 ignore_exceptions=None,
                 loglevel=logging.ERROR):
        if isinstance(url_or_request, basestring):
            self.request = requests.Request(method='GET', url=url_or_request)
        elif isinstance(url_or_request, requests.Request):
            self.request = url_or_request
        else:
            raise ValueError('url_or_request must be a string containing a URL'
                             ' or a requests.Request object')

        if ignore_exceptions:
            self.ignore_exceptions = tuple(ignore_exceptions)
        else:
            self.ignore_exceptions = (None,)

        if max_retries is not None:
            self.max_retries = int(max_retries)
        else:
            self.max_retries = None

        self.until = until
        self.error = error
        self.polling_interval = int(polling_interval)
        self.session = requests.Session()
        self.log = logging.getLogger()
        self.log.setLevel(loglevel)

    def set_conditions(self, attribute, conditions):
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
                value.append(condition)
        elif attribute == 'error' and conditions is None:
            # This is allowed
            value = None
        else:
            raise ValueError('Empty value {} for {} attribute not allowed'.format(conditions, attribute))

        if value == []:
            raise ValueError('No valid conditions for attribute "{}" provided'.format(attribute))

        setattr(self, '_{}'.format(attribute), value)

    @property
    def error(self):
        return self._error

    @error.setter
    def error(self, value):
        return self.set_conditions('error', value)

    @property
    def until(self):
        return self._until

    @until.setter
    def until(self, value):
        return self.set_conditions('until', value)

    def run(self):
        while True:
            try:
                response = self.session.send(self.request.prepare())
                for condition in self.error:
                    if self.meets_condition(response, condition):
                        raise HttSleepError(response, condition)
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

    @classmethod
    def meets_condition(response, condition):
        if condition.get('status_code') and response.status_code != condition['status_code']:
            return False
        if condition.get('json') and response.json() != condition['json']:
            return False
        if condition.get('text') and response.text != condition['text']:
            return False
        #if condition.get('jsonpath'):
        #    return False if .....
        return True


def httsleep(*args, **kwargs):
    return HttSleep(*args, **kwargs).run()
