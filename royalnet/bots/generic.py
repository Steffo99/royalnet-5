import sys
import typing
import asyncio
import logging
import sentry_sdk
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from sentry_sdk.integrations.aiohttp import AioHttpIntegration
from sentry_sdk.integrations.logging import LoggingIntegration
from ..utils import *
from ..network import *
from ..database import *
from ..commands import *
from ..error import *


log = logging.getLogger(__name__)


class GenericBot:
    """A generic bot class, to be used as base for the other more specific classes, such as
    :py:class:`royalnet.bots.TelegramBot` and :py:class:`royalnet.bots.DiscordBot`. """
    interface_name = NotImplemented

    def _init_commands(self, commands: typing.List[typing.Type[Command]]) -> None:
        """Generate the ``commands`` dictionary required to handle incoming messages, and the ``network_handlers``
        dictionary required to handle incoming requests. """
        log.debug(f"Now binding commands")
        self._Interface = self._interface_factory()
        self._Data = self._data_factory()
        self.commands = {}
        self.network_handlers: typing.Dict[str, typing.Type[NetworkHandler]] = {}
        for SelectedCommand in commands:
            log.debug(f"Binding {SelectedCommand.name}...")
            interface = self._Interface()
            self.commands[f"{interface.prefix}{SelectedCommand.name}"] = SelectedCommand(interface)
        log.debug(f"Successfully bound commands")

    def _interface_factory(self) -> typing.Type[CommandInterface]:
        # noinspection PyAbstractClass,PyMethodParameters
        class GenericInterface(CommandInterface):
            alchemy = self.alchemy
            bot = self
            loop = self.loop

            def register_net_handler(ci, message_type: str, network_handler: typing.Callable):
                self.network_handlers[message_type] = network_handler

            def unregister_net_handler(ci, message_type: str):
                del self.network_handlers[message_type]

            async def net_request(ci, request: Request, destination: str) -> dict:
                if self.network is None:
                    raise InvalidConfigError("Royalnet is not enabled on this bot")
                response_dict: dict = await self.network.request(request.to_dict(), destination)
                if "type" not in response_dict:
                    raise RoyalnetResponseError("Response is missing a type")
                elif response_dict["type"] == "ResponseSuccess":
                    response: typing.Union[ResponseSuccess, ResponseError] = ResponseSuccess.from_dict(response_dict)
                elif response_dict["type"] == "ResponseError":
                    response = ResponseError.from_dict(response_dict)
                else:
                    raise RoyalnetResponseError("Response type is unknown")
                response.raise_on_error()
                return response.data

        return GenericInterface

    def _data_factory(self) -> typing.Type[CommandData]:
        raise NotImplementedError()

    def _init_royalnet(self, royalnet_config: RoyalnetConfig):
        """Create a :py:class:`royalnet.network.RoyalnetLink`, and run it as a :py:class:`asyncio.Task`."""
        self.network: RoyalnetLink = RoyalnetLink(royalnet_config.master_uri, royalnet_config.master_secret,
                                                  self.interface_name, self._network_handler)
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
            if __debug__:
                raise
                exit(1)
            _, exc, _ = sys.exc_info()
            log.debug(f"Exception {exc} in {network_handler}")
            return ResponseError("exception_in_handler",
                                 f"An exception was raised in {network_handler} for {request.handler}. Check "
                                 f"extra_info for details.",
                                 extra_info={
                                     "type": exc.__class__.__name__,
                                     "str": str(exc)
                                 }).to_dict()

    def _init_database(self, commands: typing.List[typing.Type[Command]], database_config: DatabaseConfig):
        """Create an :py:class:`royalnet.database.Alchemy` with the tables required by the commands. Then,
        find the chain that links the ``master_table`` to the ``identity_table``. """
        log.debug(f"Initializing database")
        required_tables = {database_config.master_table, database_config.identity_table}
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
                 commands: typing.List[typing.Type[Command]] = None,
                 sentry_dsn: typing.Optional[str] = None,
                 loop: asyncio.AbstractEventLoop = None):
        if loop is None:
            self.loop = asyncio.get_event_loop()
        else:
            self.loop = loop
        if sentry_dsn:
            log.debug("Sentry integration enabled")
            self.sentry = sentry_sdk.init(sentry_dsn, integrations=[AioHttpIntegration(),
                                                                    SqlalchemyIntegration(),
                                                                    LoggingIntegration(event_level=None)])
        else:
            log.debug("Sentry integration disabled")
        try:
            if database_config is None:
                self.alchemy = None
                self.master_table = None
                self.identity_table = None
                self.identity_column = None
            else:
                self._init_database(commands=commands, database_config=database_config)
            if commands is None:
                commands = []
            self._init_commands(commands)
            if royalnet_config is None:
                self.network = None
            else:
                self._init_royalnet(royalnet_config=royalnet_config)
        except Exception as e:
            sentry_sdk.capture_exception(e)
            log.error(f"{e.__class__.__name__} while initializing Royalnet: {' | '.join(e.args)}")
            raise

    async def run(self):
        """A blocking coroutine that should make the bot start listening to commands and requests."""
        raise NotImplementedError()
