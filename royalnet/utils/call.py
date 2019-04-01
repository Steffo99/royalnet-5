import typing
import asyncio
from ..network.messages import Message
from .command import Command, CommandArgs
if typing.TYPE_CHECKING:
    from ..database import Alchemy


loop = asyncio.get_event_loop()


class Call:
    """A command call. Still an abstract class, subbots should create a new call from this."""

    # These parameters / methods should be overridden
    interface_name = NotImplemented
    interface_obj = NotImplemented
    interface_alchemy: "Alchemy" = NotImplemented

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
        self.session = None

    async def session_init(self):
        if not self.command.require_alchemy_tables:
            return
        self.session = await loop.run_in_executor(None, self.interface_alchemy.Session)

    async def session_end(self):
        if not self.session:
            return
        self.session.close()

    async def run(self):
        await self.session_init()
        try:
            coroutine = getattr(self.command, self.interface_name)
        except AttributeError:
            coroutine = getattr(self.command, "common")
        try:
            result = await coroutine(self.command, self, CommandArgs(*self.args, **self.kwargs))
        finally:
            await self.session_end()
        return result
