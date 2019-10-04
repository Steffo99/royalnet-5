class CommandError(Exception):
    """Something went wrong during the execution of this command.

    Display an error message to the user, explaining what went wrong."""
    def __init__(self, message=""):
        self.message = message

    def __repr__(self):
        return f"{self.__class__.__qualname__}({repr(self.message)})"


class InvalidInputError(CommandError):
    """The command has received invalid input and cannot complete.

    Display an error message to the user, along with the correct syntax for the command."""


class UnsupportedError(CommandError):
    """A requested feature is not available on this interface.

    Display an error message to the user, telling them to use another interface."""


class KeyboardExpiredError(CommandError):
    """A special type of exception that can be raised in keyboard handlers to mark a specific keyboard as expired."""
