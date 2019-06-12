import typing
import asyncio
from .command import Command
from .commandargs import CommandArgs
if typing.TYPE_CHECKING:
    from ..database import Alchemy


class Call:
    """A command call. An abstract class, sub-bots should create a new call class from this.
    
    Attributes:
        interface_name: The name of the interface that is calling the command. For example, ``telegram``, or ``discord``.
        interface_obj: The main object of the interface that is calling the command. For example, the :py:class:`royalnet.bots.TelegramBot` object.
        interface_prefix: The command prefix used by the interface. For example, ``/``, or ``!``.
        alchemy: The :py:class:`royalnet.database.Alchemy` object associated to this interface. May be None if the interface is not connected to any database."""

    # These parameters / methods should be overridden
    interface_name = NotImplemented
    interface_obj = NotImplemented
    interface_prefix = NotImplemented
    alchemy: "Alchemy" = NotImplemented

    async def reply(self, text: str) -> None:
        """Send a text message to the channel where the call was made.

        Parameters:
             text: The text to be sent, possibly formatted in the weird undescribed markup that I'm using."""
        raise NotImplementedError()

    async def net_request(self, message, destination: str) -> dict:
        """Send data through a :py:class:`royalnet.network.RoyalnetLink` and wait for a :py:class:`royalnet.network.Reply`.

        Parameters:
            message: The data to be sent. Must be :py:mod:`pickle`-able.
            destination: The destination of the request, either in UUID format or node name."""
        raise NotImplementedError()

    async def get_author(self, error_if_none=False):
        """Try to find the universal identifier of the user that sent the message.
        That probably means, the database row identifying the user.

        Parameters:
            error_if_none: Raise a :py:exc:`royalnet.error.UnregisteredError` if this is True and the call has no author.

        Raises:
             :py:exc:`royalnet.error.UnregisteredError` if ``error_if_none`` is set to True and no author is found."""
        raise NotImplementedError()

    # These parameters / methods should be left alone
    def __init__(self,
                 channel,
                 command: typing.Type[Command],
                 command_args: typing.List[str] = None,
                 loop: asyncio.AbstractEventLoop = None,
                 **kwargs):
        """Create the call.

        Parameters:
            channel: The channel object this call was sent in.
            command: The command to be called.
            command_args: The arguments to be passed to the command
            kwargs: Additional optional keyword arguments that may be passed to the command, possibly specific to the bot.
            """
        if command_args is None:
            command_args = []
        if loop is None:
            self.loop = asyncio.get_event_loop()
        else:
            self.loop = loop
        self.channel = channel
        self.command = command
        self.args = CommandArgs(command_args)
        self.kwargs = kwargs
        self.session = None

    async def _session_init(self):
        """If the command requires database access, create a :py:class:`royalnet.database.Alchemy` session for this call, otherwise, do nothing."""
        if not self.command.require_alchemy_tables:
            return
        self.session = await self.loop.run_in_executor(None, self.alchemy.Session)

    async def session_end(self):
        """Close the previously created :py:class:`royalnet.database.Alchemy` session for this call (if it was created)."""
        if not self.session:
            return
        self.session.close()

    async def run(self):
        """Execute the called command, and return the command result."""
        await self._session_init()
        try:
            coroutine = getattr(self.command, self.interface_name)
        except AttributeError:
            coroutine = self.command.common
        try:
            result = await coroutine(self)
        finally:
            await self.session_end()
        return result
