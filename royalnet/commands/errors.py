class CommandError(Exception):
    """Something went wrong during the execution of this command.

    Display an error message to the user, explaining what went wrong."""
    def __init__(self, message=""):
        self.message = message

    def __repr__(self):
        return f"{self.__class__.__qualname__}({repr(self.message)})"


class UserError(CommandError):
    """The command failed to execute, and the error is because of something that the user did."""


class InvalidInputError(UserError):
    """The command has received invalid input and cannot complete."""


class UnsupportedError(CommandError):
    """A requested feature is not available on this interface."""


class ConfigurationError(CommandError):
    """The command cannot work because of a wrong configuration by part of the Royalnet admin."""


class ExternalError(CommandError):
    """The command failed to execute, but the problem was because of an external factor (such as an external API going
    down)."""


class ProgramError(CommandError):
    """The command encountered an error in the program."""
