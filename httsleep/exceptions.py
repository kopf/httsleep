class Alarm(Exception):
    def __init__(self, response, alarm_condition):
        self.response = response
        self.alarm = alarm_condition
        self.mesg = 'Response matched an error condition: {}'.format(alarm_condition)