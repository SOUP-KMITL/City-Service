class ServiceException(Exception):
    def __init__(self, http_code, message):
        super(ServiceException, self).__init__(message)
        self.message = message
        self.http_code = http_code
