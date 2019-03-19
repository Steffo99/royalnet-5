class Message:
    def __repr__(self):
        return f"<{self.__class__.__name__}>"


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
