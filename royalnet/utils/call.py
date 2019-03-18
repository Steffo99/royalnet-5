import typing
from ..network.messages import Message
from .command import Command, CommandArgs


class Call:
    """A command call. Still an abstract class, subbots should create a new call from this."""

    # These parameters / methods should be overridden
    interface_name = NotImplemented
    interface_obj = NotImplemented

    async def reply(self, text: str):
        """Send a text message to the channel the call was made."""
        raise NotImplementedError()

    async def net_request(self, message: Message, destination: str):
        """Send data to the rest of the Royalnet, and optionally wait for an answer.
        The data must be pickleable."""
        raise NotImplementedError()

    # These parameters / methods should be left alone
    def __init__(self, channel, command: Command, *args, **kwargs):
        self.channel = channel
        self.command = command
        self.args = args
        self.kwargs = kwargs

    async def run(self):
        try:
            coroutine = getattr(self.command, self.interface_name)
        except AttributeError:
            coroutine = getattr(self.command, "common")
        return await coroutine(self.command, self, CommandArgs(*self.args, **self.kwargs))
