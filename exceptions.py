
class BaseError(Exception):
    def __init__(self, value):
        self.parameter = value

    def __str__(self):
        return repr(self.parameter)


class InvalidUrlError(BaseError):
    pass


class InvalidInputError(BaseError):
    pass


class InvalidHostError(BaseError):
    pass


class InvalidRequestError(BaseError):
    pass


class InvalidNodeError(BaseError):
    pass


class EmptyQueueError(BaseError):
    pass

class UrlNotInDatabaseError(BaseError):
    pass

class MultipleUrlsInDatabaseError(BaseError):
    pass

class UrlPresentInDatabaseError(BaseError):
    pass

class HostInLinkedByError(BaseError):
    pass

class ServerNotRunningError(BaseError):
    pass

class StreamTimedOutError(BaseError):
    pass