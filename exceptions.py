
class BaseError(Exception):
    def __init__(self, value):
        self.parameter = value

    def __str__(self):
        return repr(self.parameter)


class InvalidURLException(BaseError):
    pass


class InvalidInputException(BaseError):
    pass


class InvalidHostException(BaseError):
    pass


class InvalidRequestException(BaseError):
    pass


class InvalidNodeException(BaseError):
    pass


class EmptyQueueException(BaseError):
    pass