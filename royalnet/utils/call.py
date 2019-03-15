import typing
from .command import Command


class Call:
    """A command call. Still an abstract class, subbots should create a new call from this."""

    # These parameters / methods should be overridden
    interface_name = NotImplemented
    interface_obj = NotImplemented

    async def reply(self, text: str):
        """Send a text message to the channel the call was made."""
        raise NotImplementedError()

    # These parameters / methods should be left alone
    def __init__(self, channel, command: Command, parameters: typing.List[str]=None):
        self.channel = channel
        self.command = command
        if parameters is None:
            self.parameters = []
        else:
            self.parameters = parameters

    async def run(self, *args, **kwargs):
        try:
            coroutine = getattr(self.command, self.interface_name)
        except AttributeError:
            coroutine = getattr(self.command, "common")
        return await coroutine(self.command, self, *args, **kwargs)
