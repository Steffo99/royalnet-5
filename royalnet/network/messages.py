class Message:
    pass


class IdentifySuccessfulMessage(Message):
    pass


class ErrorMessage(Message):
    def __init__(self, reason):
        super().__init__()
        self.reason = reason


class BadMessage(ErrorMessage):
    pass


class InvalidSecretErrorMessage(BadMessage):
    pass
