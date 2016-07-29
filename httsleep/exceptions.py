class HttSleepError(Exception):
    def __init__(self, response, error_condition):
        self.response = response
        self.error_condition = error_condition
        self.mesg = 'Response matched an error condition: {}'.format(error_condition)