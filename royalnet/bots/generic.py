import sys
import typing
import asyncio
import logging
from ..utils import Command, NetworkHandler, Call
from ..commands import NullCommand
from ..network import RoyalnetLink, Request, Response, ResponseError, RoyalnetConfig
from ..database import Alchemy, DatabaseConfig, relationshiplinkchain


log = logging.getLogger(__name__)


class GenericBot:
    """A generic bot class, to be used as base for the other more specific classes, such as :ref:`royalnet.bots.TelegramBot` and :ref:`royalnet.bots.DiscordBot`."""
    interface_name = NotImplemented

    def _init_commands(self,
                       command_prefix: str,
                       commands: typing.List[typing.Type[Command]],
                       missing_command: typing.Type[Command],
                       error_command: typing.Type[Command]) -> None:
        """Generate the ``commands`` dictionary required to handle incoming messages, and the ``network_handlers`` dictionary required to handle incoming requests."""
        log.debug(f"Now generating commands")
        self.command_prefix = command_prefix
        self.commands: typing.Dict[str, typing.Type[Command]] = {}
        self.network_handlers: typing.Dict[str, typing.Type[NetworkHandler]] = {}
        for command in commands:
            lower_command_name = command.command_name.lower()
            self.commands[f"{command_prefix}{lower_command_name}"] = command
            self.network_handlers = {**self.network_handlers, **command.network_handler_dict()}
        self.missing_command: typing.Type[Command] = missing_command
        self.error_command: typing.Type[Command] = error_command
        log.debug(f"Successfully generated commands")

    def _call_factory(self) -> typing.Type[Call]:
        """Create the TelegramCall class, representing a command call. It should inherit from :py:class:`royalnet.utils.Call`.

        Returns:
            The created TelegramCall class."""
        raise NotImplementedError()

    def _init_royalnet(self, royalnet_config: RoyalnetConfig):
        """Create a :py:class:`royalnet.network.RoyalnetLink`, and run it as a :py:class:`asyncio.Task`."""
        self.network: RoyalnetLink = RoyalnetLink(royalnet_config.master_uri, royalnet_config.master_secret, self.interface_name,
                                                  self._network_handler)
        log.debug(f"Running RoyalnetLink {self.network}")
        self.loop.create_task(self.network.run())

    async def _network_handler(self, request_dict: dict) -> dict:
        """Handle a single :py:class:`dict` received from the :py:class:`royalnet.network.RoyalnetLink`.

        Returns:
            Another :py:class:`dict`, formatted as a :py:class:`royalnet.network.Response`."""
        # Convert the dict to a Request
        try:
            request: Request = Request.from_dict(request_dict)
        except TypeError:
            log.warning(f"Invalid request received: {request_dict}")
            return ResponseError("invalid_request",
                                 f"The Request that you sent was invalid. Check extra_info to see what you sent.",
                                 extra_info={"you_sent": request_dict}).to_dict()
        log.debug(f"Received {request} from the RoyalnetLink")
        try:
            network_handler = self.network_handlers[request.handler]
        except KeyError:
            log.warning(f"Missing network_handler for {request.handler}")
            return ResponseError("no_handler", f"This Link is missing a network handler for {request.handler}.").to_dict()
        try:
            log.debug(f"Using {network_handler} as handler for {request.handler}")
            response: Response = await getattr(network_handler, self.interface_name)(self, request.data)
            return response.to_dict()
        except Exception:
            _, exc, _ = sys.exc_info()
            log.debug(f"Exception {exc} in {network_handler}")
            return ResponseError("exception_in_handler",
                                 f"An exception was raised in {network_handler} for {request.handler}. Check extra_info for details.",
                                 extra_info={
                                     "type": exc.__class__.__name__,
                                     "str": str(exc)
                                 }).to_dict()

    def _init_database(self, commands: typing.List[typing.Type[Command]], database_config: DatabaseConfig):
        """Create an :py:class:`royalnet.database.Alchemy` with the tables required by the commands. Then, find the chain that links the ``master_table`` to the ``identity_table``."""
        log.debug(f"Initializing database")
        required_tables = set()
        for command in commands:
            required_tables = required_tables.union(command.require_alchemy_tables)
        log.debug(f"Found {len(required_tables)} required tables")
        self.alchemy = Alchemy(database_config.database_uri, required_tables)
        self.master_table = self.alchemy.__getattribute__(database_config.master_table.__name__)
        self.identity_table = self.alchemy.__getattribute__(database_config.identity_table.__name__)
        self.identity_column = self.identity_table.__getattribute__(self.identity_table,
                                                                    database_config.identity_column_name)
        self.identity_chain = relationshiplinkchain(self.master_table, self.identity_table)
        log.debug(f"Identity chain is {self.identity_chain}")

    def __init__(self, *,
                 royalnet_config: typing.Optional[RoyalnetConfig] = None,
                 database_config: typing.Optional[DatabaseConfig] = None,
                 command_prefix: str,
                 commands: typing.List[typing.Type[Command]] = None,
                 missing_command: typing.Type[Command] = NullCommand,
                 error_command: typing.Type[Command] = NullCommand,
                 loop: asyncio.AbstractEventLoop = None):
        if loop is None:
            self.loop = asyncio.get_event_loop()
        else:
            self.loop = loop
        if database_config is None:
            self.alchemy = None
            self.master_table = None
            self.identity_table = None
            self.identity_column = None
        else:
            self._init_database(commands=commands, database_config=database_config)
        if commands is None:
            commands = []
        self._init_commands(command_prefix, commands, missing_command=missing_command, error_command=error_command)
        self._Call = self._call_factory()
        if royalnet_config is None:
            self.network = None
        else:
            self._init_royalnet(royalnet_config=royalnet_config)

    async def call(self, command_name: str, channel, parameters: typing.List[str] = None, **kwargs):
        """Call the command with the specified name.

        If it doesn't exist, call ``self.missing_command``.

        If an exception is raised during the execution of the command, call ``self.error_command``."""
        log.debug(f"Trying to call {command_name}")
        if parameters is None:
            parameters = []
        try:
            command: typing.Type[Command] = self.commands[command_name]
        except KeyError:
            log.debug(f"Calling missing_command because {command_name} does not exist")
            command = self.missing_command
        try:
            await self._Call(channel, command, parameters, **kwargs).run()
        except Exception as exc:
            log.debug(f"Calling error_command because of an error in {command_name}")
            await self._Call(channel, self.error_command,
                             exception=exc,
                             previous_command=command, **kwargs).run()

    async def run(self):
        """A blocking coroutine that should make the bot start listening to commands and requests."""
        raise NotImplementedError()
