class Message:
    def __repr__(self):
        return f"<{self.__class__.__name__}>"


class IdentifySuccessfulMessage(Message):
    pass


class ServerErrorMessage(Message):
    def __init__(self, reason):
        super().__init__()
        self.reason = reason


class InvalidSecretEM(ServerErrorMessage):
    pass


class InvalidPackageEM(ServerErrorMessage):
    pass


class InvalidDestinationEM(InvalidPackageEM):
    pass


class RequestSuccessful(Message):
    pass


class RequestError(Message):
    def __init__(self, exc: Exception):
        self.exc = exc
