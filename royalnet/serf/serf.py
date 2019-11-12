import asyncio
import logging
from typing import Type, Optional, Awaitable, Dict, List, Any, Callable, Union
import sentry_sdk
import keyring
from royalnet.herald import Response, ResponseSuccess, Broadcast, ResponseFailure, Request, Link
from royalnet.herald import Config as HeraldConfig
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from sentry_sdk.integrations.aiohttp import AioHttpIntegration
from sentry_sdk.integrations.logging import LoggingIntegration
from royalnet.commands import Command, CommandInterface, CommandData, CommandError, UnsupportedError
from royalnet.alchemy import Alchemy
from .alchemyconfig import AlchemyConfig


log = logging.getLogger(__name__)


class Serf:
    """An abstract class, to be used as base to implement Royalnet bots on multiple interfaces (such as Telegram or
    Discord)."""
    interface_name = NotImplemented

    def __init__(self, *,
                 alchemy_config: Optional[AlchemyConfig] = None,
                 commands: List[Type[Command]] = None,
                 network_config: Optional[HeraldConfig] = None,
                 sentry_dsn: Optional[str] = None,
                 loop: asyncio.AbstractEventLoop = None,
                 secrets_name: str = "__default__"):
        self.secrets_name = secrets_name

        if alchemy_config is not None:
            self.init_alchemy(alchemy_config)

        self.Interface: Type[CommandInterface] = self.interface_factory()
        """The :class:`CommandInterface` class of this Serf."""

        self.Data: Type[CommandData] = self.data_factory()
        """The :class:`CommandData` class of this Serf."""

        self.commands: Dict[str, Command] = {}
        """The :class:`dict` connecting each command name to its :class:`Command` object."""

        if commands is None:
            commands = []
        self.register_commands(commands)

        self.herald_handlers: Dict[str, Callable[["Serf", Any], Awaitable[Optional[dict]]]] = {}
        """A :class:`dict` linking :class:`Request` event names to coroutines returning a :class:`dict` that will be
        sent as :class:`Response` to the event."""

        self.herald: Optional[Link] = None
        """The :class:`Link` object connecting the Serf to the rest of the herald network."""

        self.herald_task: Optional[asyncio.Task] = None
        """A reference to the :class:`asyncio.Task` that runs the :class:`Link`."""

        if network_config is not None:
            self.init_network(network_config)

    def interface_factory(self) -> Type[CommandInterface]:
        """Create the :class:`CommandInterface` class for the Serf."""
        # noinspection PyMethodParameters
        class GenericInterface(CommandInterface):
            alchemy: Alchemy = self.alchemy
            bot: "Serf" = self
            loop: asyncio.AbstractEventLoop = self.loop

            def register_herald_action(ci,
                                       event_name: str,
                                       coroutine: Callable[[Any], Awaitable[Dict]]) -> None:
                """Allow a coroutine to be called when a :class:`royalherald.Request` is received."""
                if self.herald is None:
                    raise UnsupportedError("`royalherald` is not enabled on this bot.")
                self.herald_handlers[event_name] = coroutine

            def unregister_herald_action(ci, event_name: str):
                """Disable a previously registered coroutine from being called on reception of a
                :class:`royalherald.Request`."""
                if self.herald is None:
                    raise UnsupportedError("`royalherald` is not enabled on this bot.")
                del self.herald_handlers[event_name]

            async def call_herald_action(ci, destination: str, event_name: str, args: Dict) -> Dict:
                """Send a :class:`royalherald.Request` to a specific destination, and wait for a
                :class:`royalherald.Response`."""
                if self.herald is None:
                    raise UnsupportedError("`royalherald` is not enabled on this bot.")
                request: Request = Request(handler=event_name, data=args)
                response: Response = await self.herald.request(destination=destination, request=request)
                if isinstance(response, ResponseFailure):
                    if response.extra_info["type"] == "CommandError":
                        raise CommandError(response.extra_info["message"])
                    # TODO: change exception type
                    raise Exception(f"Herald action call failed:\n"
                                    f"[p]{response}[/p]")
                elif isinstance(response, ResponseSuccess):
                    return response.data
                else:
                    raise TypeError(f"Other Herald Link returned unknown response:\n"
                                    f"[p]{response}[/p]")

        return GenericInterface

    def data_factory(self) -> Type[CommandData]:
        """Create the :class:`CommandData` for the Serf."""
        raise NotImplementedError()

    def register_commands(self, commands: List[Type[Command]]) -> None:
        """Initialize and register all commands passed as argument.

        If called again during the execution of the bot, all current commands will be replaced with the new ones.

        Warning:
            Hot-replacing commands was never tested and probably doesn't work."""
        log.info(f"Registering {len(commands)} commands...")
        # Instantiate the Commands
        for SelectedCommand in commands:
            # Warn if the command would be overriding something
            if f"{self.Interface.prefix}{SelectedCommand.name}" in self.commands:
                log.warning(f"Overriding (already defined): "
                            f"{SelectedCommand.__qualname__} -> {self.Interface.prefix}{SelectedCommand.name}")
            else:
                log.debug(f"Registering: "
                          f"{SelectedCommand.__qualname__} -> {self.Interface.prefix}{SelectedCommand.name}")
            # Create a new interface
            interface = self.Interface()
            # Try to instantiate the command
            try:
                command = SelectedCommand(interface)
            except Exception as e:
                log.error(f"Skipping: "
                          f"{SelectedCommand.__qualname__} - {e.__class__.__qualname__} in the initialization.")
                sentry_sdk.capture_exception(e)
                continue
            # Link the interface to the command
            interface.command = command
            # Register the command in the commands dict
            self.commands[f"{interface.prefix}{SelectedCommand.name}"] = command
            # Register aliases, but don't override anything
            for alias in SelectedCommand.aliases:
                if f"{interface.prefix}{alias}" not in self.commands:
                    log.debug(f"Aliasing: {SelectedCommand.__qualname__} -> {interface.prefix}{alias}")
                    self.commands[f"{interface.prefix}{alias}"] = \
                        self.commands[f"{interface.prefix}{SelectedCommand.name}"]
                else:
                    log.info(f"Ignoring (already defined): {SelectedCommand.__qualname__} -> {interface.prefix}{alias}")

    def init_network(self, config: HeraldConfig):
        """Create a :py:class:`Link`, and run it as a :py:class:`asyncio.Task`."""
        log.debug(f"Initializing herald...")
        self.herald: Link = Link(config, self._network_handler)
        self.herald_task = self.loop.create_task(self.herald.run())

    async def _network_handler(self, message: Union[Request, Broadcast]) -> Response:
        try:
            network_handler = self.herald_handlers[message.handler]
        except KeyError:
            log.warning(f"Missing network_handler for {message.handler}")
            return ResponseFailure("no_handler", f"This bot is missing a network handler for {message.handler}.")
        else:
            log.debug(f"Using {network_handler} as handler for {message.handler}")
        if isinstance(message, Request):
            try:
                response_data = await network_handler(self, **message.data)
                return ResponseSuccess(data=response_data)
            except Exception as e:
                sentry_sdk.capture_exception(e)
                log.error(f"Exception {e} in {network_handler}")
                return ResponseFailure("exception_in_handler",
                                       f"An exception was raised in {network_handler} for {message.handler}.",
                                       extra_info={
                                          "type": e.__class__.__name__,
                                          "message": str(e)
                                       })
        elif isinstance(message, Broadcast):
            await network_handler(self, **message.data)

    def _init_database(self):
        """Create an :py:class:`royalnet.database.Alchemy` with the tables required by the packs. Then,
        find the chain that links the ``master_table`` to the ``identity_table``. """
        if self.uninitialized_database_config:
            log.info(f"Alchemy: enabled")
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
            self.identity_chain = table_dfs(self.master_table, self.identity_table)
            log.debug(f"Identity chain: {' -> '.join([str(item) for item in self.identity_chain])}")
        else:
            log.info(f"Alchemy: disabled")
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
            self.init_network()
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
