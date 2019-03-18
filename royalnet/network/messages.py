class Message:
    pass


class IdentifySuccessfulMessage(Message):
    pass


class ErrorMessage(Message):
    def __init__(self, reason):
        super().__init__()
        self.reason = reason


class InvalidSecretEM(ErrorMessage):
    pass


class InvalidPackageEM(ErrorMessage):
    pass


class InvalidDestinationEM(InvalidPackageEM):
    pass


