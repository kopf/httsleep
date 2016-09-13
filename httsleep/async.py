import asyncio
import logging

from .main import DEFAULT_MAX_RETRIES, DEFAULT_POLLING_INTERVAL, HttSleeper
from .exceptions import Alarm


class AsyncHttSleeper(HttSleeper):
    def run(self):
        loop = asyncio.get_event_loop()
        while True:
            try:
                future = loop.run_in_executor(None, self.session.send, self.request.prepare())
                response = yield from future
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
            yield from asyncio.sleep(self.polling_interval)


@asyncio.coroutine
def async_httsleep(url_or_request, until=None, alarms=None,
                   status_code=None, json=None, jsonpath=None, text=None, callback=None,
                   auth=None, headers=None,
                   polling_interval=DEFAULT_POLLING_INTERVAL,
                   max_retries=DEFAULT_MAX_RETRIES,
                   ignore_exceptions=None, loglevel=logging.ERROR):
    return AsyncHttSleeper(
        url_or_request, until=until, alarms=alarms, status_code=status_code,
        json=json, jsonpath=jsonpath, text=text, callback=callback,
        auth=auth, headers=headers, polling_interval=polling_interval,
        max_retries=max_retries, ignore_exceptions=ignore_exceptions,
        loglevel=loglevel
    ).run()
