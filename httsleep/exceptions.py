class Alarm(Exception):
    """ Exception raised when an alarm condition has been met. Contains the following
    extra attributes:

    * response: The response the matched the alarm condition
    * alarm: The alarm condition that was triggered
    """
    def __init__(self, response, alarm_condition):
        self.response = response
        self.alarm = alarm_condition
        self.mesg = 'Response matched an error condition: {}'.format(alarm_condition)
