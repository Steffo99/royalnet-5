class NoneFoundError(Exception):
    """The element that was being looked for was not found."""


class TooManyFoundError(Exception):
    """Multiple elements matching the request were found, and only one was expected."""


class UnregisteredError(Exception):
    """The command required a registered user, and the user was not registered."""


class UnsupportedError(Exception):
    """The command is not supported for the specified interface."""


class InvalidInputError(Exception):
    """The command has received invalid input and cannot complete."""


class InvalidConfigError(Exception):
    """The bot has not been configured correctly, therefore the command can not function."""


class ExternalError(Exception):
    """Something went wrong in a non-Royalnet component and the command execution cannot be completed."""
