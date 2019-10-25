import sys
import asyncio
import logging
import sentry_sdk
import keyring
import royalnet.version
import royalherald as rh
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from sentry_sdk.integrations.aiohttp import AioHttpIntegration
from sentry_sdk.integrations.logging import LoggingIntegration
from ..utils import *
from ..database import *
from ..commands import *
from ..error import *


log = logging.getLogger(__name__)


class GenericBot:
    """A common bot class, to be used as base for the other more specific classes, such as
    :py:class:`royalnet.bots.TelegramBot` and :py:class:`royalnet.bots.DiscordBot`. """
    interface_name = NotImplemented

    def _init_commands(self) -> None:
        """Generate the ``packs`` dictionary required to handle incoming messages, and the ``network_handlers``
        dictionary required to handle incoming requests. """
        log.info(f"Registering packs...")
        self._Interface = self._interface_factory()
        self._Data = self._data_factory()
        self.commands = {}
        self.network_handlers: typing.Dict[str, typing.Callable[["GenericBot", typing.Any],
                                                                typing.Awaitable[typing.Optional[typing.Dict]]]] = {}
        for SelectedCommand in self.uninitialized_commands:
            interface = self._Interface()
            try:
                command = SelectedCommand(interface)
            except Exception as e:
                log.error(f"{e.__class__.__qualname__} during the registration of {SelectedCommand.__qualname__}")
                continue
            # Linking the command to the interface
            interface.command = command
            # Override the main command name, but warn if it's overriding something
            if f"{interface.prefix}{SelectedCommand.name}" in self.commands:
                log.warning(f"Overriding (already defined): {SelectedCommand.__qualname__} -> {interface.prefix}{SelectedCommand.name}")
            else:
                log.debug(f"Registering: {SelectedCommand.__qualname__} -> {interface.prefix}{SelectedCommand.name}")
            self.commands[f"{interface.prefix}{SelectedCommand.name}"] = command
            # Register aliases, but don't override anything
            for alias in SelectedCommand.aliases:
                if f"{interface.prefix}{alias}" not in self.commands:
                    log.debug(f"Aliasing: {SelectedCommand.__qualname__} -> {interface.prefix}{alias}")
                    self.commands[f"{interface.prefix}{alias}"] = self.commands[f"{interface.prefix}{SelectedCommand.name}"]
                else:
                    log.info(f"Ignoring (already defined): {SelectedCommand.__qualname__} -> {interface.prefix}{alias}")

    def _interface_factory(self) -> typing.Type[CommandInterface]:
        # noinspection PyAbstractClass,PyMethodParameters
        class GenericInterface(CommandInterface):
            alchemy = self.alchemy
            bot = self
            loop = self.loop

            def register_herald_action(ci,
                                       event_name: str,
                                       coroutine: typing.Callable[[typing.Any], typing.Awaitable[typing.Dict]]) -> None:
                self.network_handlers[event_name] = coroutine

            def unregister_herald_action(ci, event_name: str):
                del self.network_handlers[event_name]

            async def call_herald_action(ci, destination: str, event_name: str, args: typing.Dict) -> typing.Dict:
                if self.network is None:
                    raise UnsupportedError("Herald is not enabled on this bot")
                request: rh.Request = rh.Request(handler=event_name, data=args)
                response: rh.Response = await self.network.request(destination=destination, request=request)
                if isinstance(response, rh.ResponseFailure):
                    if response.extra_info["type"] == "CommandError":
                        raise CommandError(response.extra_info["message"])
                    raise CommandError(f"Herald action call failed:\n"
                                       f"[p]{response}[/p]")
                elif isinstance(response, rh.ResponseSuccess):
                    return response.data
                else:
                    raise TypeError(f"Other Herald Link returned unknown response:\n"
                                    f"[p]{response}[/p]")

        return GenericInterface

    def _data_factory(self) -> typing.Type[CommandData]:
        raise NotImplementedError()

    def _init_network(self):
        """Create a :py:class:`royalherald.Link`, and run it as a :py:class:`asyncio.Task`."""
        if self.uninitialized_network_config is not None:
            self.network: rh.Link = rh.Link(self.uninitialized_network_config.master_uri,
                                            self.uninitialized_network_config.master_secret,
                                            self.interface_name,
                                            self._network_handler)
            log.debug(f"Running NetworkLink {self.network}")
            self.loop.create_task(self.network.run())

    async def _network_handler(self, message: typing.Union[rh.Request, rh.Broadcast]) -> rh.Response:
        try:
            network_handler = self.network_handlers[message.handler]
        except KeyError:
            log.warning(f"Missing network_handler for {message.handler}")
            return rh.ResponseFailure("no_handler", f"This bot is missing a network handler for {message.handler}.")
        else:
            log.debug(f"Using {network_handler} as handler for {message.handler}")
        if isinstance(message, rh.Request):
            try:
                response_data = await network_handler(self, **message.data)
                return rh.ResponseSuccess(data=response_data)
            except Exception as e:
                sentry_sdk.capture_exception(e)
                log.error(f"Exception {e} in {network_handler}")
                return rh.ResponseFailure("exception_in_handler",
                                          f"An exception was raised in {network_handler} for {message.handler}.",
                                          extra_info={
                                              "type": e.__class__.__name__,
                                              "message": str(e)
                                          })
        elif isinstance(message, rh.Broadcast):
            await network_handler(self, **message.data)

    def _init_database(self):
        """Create an :py:class:`royalnet.database.Alchemy` with the tables required by the packs. Then,
        find the chain that links the ``master_table`` to the ``identity_table``. """
        if self.uninitialized_database_config:
            log.info(f"Database: enabled")
            required_tables = {self.uninitialized_database_config.master_table, self.uninitialized_database_config.identity_table}
            for command in self.uninitialized_commands:
                required_tables = required_tables.union(command.tables)
            log.debug(f"Required tables: {', '.join([item.__qualname__ for item in required_tables])}")
            self.alchemy = Alchemy(self.uninitialized_database_config.database_uri, required_tables)
            self.master_table = self.alchemy.__getattribute__(self.uninitialized_database_config.master_table.__name__)
            log.debug(f"Master table: {self.master_table.__qualname__}")
            self.identity_table = self.alchemy.__getattribute__(self.uninitialized_database_config.identity_table.__name__)
            log.debug(f"Identity table: {self.identity_table.__qualname__}")
            self.identity_column = self.identity_table.__getattribute__(self.identity_table,
                                                                        self.uninitialized_database_config.identity_column_name)
            log.debug(f"Identity column: {self.identity_column.__class__.__qualname__}")
            self.identity_chain = relationshiplinkchain(self.master_table, self.identity_table)
            log.debug(f"Identity chain: {' -> '.join([str(item) for item in self.identity_chain])}")
        else:
            log.debug(f"Database: disabled")
            self.alchemy = None
            self.master_table = None
            self.identity_table = None
            self.identity_column = None

    def _init_sentry(self):
        if self.uninitialized_sentry_dsn:
            # noinspection PyUnreachableCode
            if __debug__:
                release = "DEV"
            else:
                release = royalnet.version.semantic
            log.info(f"Sentry: enabled (Royalnet {release})")
            self.sentry = sentry_sdk.init(self.uninitialized_sentry_dsn,
                                          integrations=[AioHttpIntegration(),
                                                        SqlalchemyIntegration(),
                                                        LoggingIntegration(event_level=None)],
                                          release=release)
        else:
            log.info("Sentry: disabled")

    def _init_loop(self):
        if self.uninitialized_loop is None:
            self.loop = asyncio.get_event_loop()
        else:
            self.loop = self.uninitialized_loop

    def __init__(self, *,
                 network_config: typing.Optional[rh.Config] = None,
                 database_config: typing.Optional[DatabaseConfig] = None,
                 commands: typing.List[typing.Type[Command]] = None,
                 sentry_dsn: typing.Optional[str] = None,
                 loop: asyncio.AbstractEventLoop = None,
                 secrets_name: str = "__default__"):
        self.initialized = False
        self.uninitialized_network_config = network_config
        self.uninitialized_database_config = database_config
        self.uninitialized_commands = commands
        self.uninitialized_sentry_dsn = sentry_dsn
        self.uninitialized_loop = loop
        self.secrets_name = secrets_name

    def get_secret(self, username: str):
        return keyring.get_password(f"Royalnet/{self.secrets_name}", username)

    def set_secret(self, username: str, password: str):
        return keyring.set_password(f"Royalnet/{self.secrets_name}", username, password)

    def _initialize(self):
        if not self.initialized:
            self._init_sentry()
            self._init_loop()
            self._init_database()
            self._init_commands()
            self._init_network()
            self.initialized = True

    def run(self):
        """A blocking coroutine that should make the bot start listening to packs and requests."""
        raise NotImplementedError()

    def run_blocking(self, verbose=False):
        if verbose:
            core_logger = logging.root
            core_logger.setLevel(logging.DEBUG)
            stream_handler = logging.StreamHandler()
            stream_handler.formatter = logging.Formatter("{asctime}\t{name}\t{levelname}\t{message}", style="{")
            core_logger.addHandler(stream_handler)
            core_logger.debug("Logging setup complete.")
        self._initialize()
        self.loop.run_until_complete(self.run())
