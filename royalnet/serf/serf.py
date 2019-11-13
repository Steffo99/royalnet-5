import logging
from asyncio import Task, AbstractEventLoop
from typing import Type, Optional, Awaitable, Dict, List, Any, Callable, Union, Set
from keyring import get_password
import sentry_sdk
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from sentry_sdk.integrations.aiohttp import AioHttpIntegration
from sentry_sdk.integrations.logging import LoggingIntegration
from sqlalchemy.schema import Table
from royalnet import __version__ as version
from royalnet.commands import Command, CommandInterface, CommandData, CommandError, UnsupportedError
from royalnet.alchemy import Alchemy, table_dfs
from royalnet.herald import Response, ResponseSuccess, Broadcast, ResponseFailure, Request, Link
from royalnet.herald import Config as HeraldConfig
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
                 secrets_name: str = "__default__"):
        self.secrets_name = secrets_name

        self.alchemy: Optional[Alchemy] = None
        """The :class:`Alchemy` object connecting this Serf to the database."""

        self._master_table: Optional[Table] = None
        """The central table listing all users. It usually is :class:`User`."""

        self._identity_table: Optional[Table] = None
        """The identity table containing the interface data (such as the Telegram user data) and that is in a 
        many-to-one relationship with the master table."""

        # TODO: I'm not sure what this is either
        self._identity_column: Optional[str] = None

        if alchemy_config is not None:
            tables = self.find_tables(alchemy_config, commands)
            self.init_alchemy(alchemy_config, tables)

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

        self.herald_task: Optional[Task] = None
        """A reference to the :class:`asyncio.Task` that runs the :class:`Link`."""

        if network_config is not None:
            self.init_network(network_config)

        self.loop: Optional[AbstractEventLoop] = None
        """The event loop this Serf is running on."""

    @staticmethod
    def find_tables(alchemy_config: AlchemyConfig, commands: List[Type[Command]]) -> Set[type]:
        """Find the :class:`Table`s required by the Serf.

        Warning:
            This function will return a wrong result if there are tables between the master table and the identity table
            that aren't included by a command.

        Returns:
            A :class:`list` of :class:`Table`s."""
        # FIXME: breaks if there are nonincluded tables between master and identity.
        tables = {alchemy_config.master_table, alchemy_config.identity_table}
        for command in commands:
            tables = tables.union(command.tables)
        return tables

    def init_alchemy(self, alchemy_config: AlchemyConfig, tables: Set[type]) -> None:
        """Create and initialize the :class:`Alchemy` with the required tables, and find the link between the master
        table and the identity table."""
        self.alchemy = Alchemy(alchemy_config.database_url, tables)
        self._master_table = self.alchemy.get(alchemy_config.master_table)
        self._identity_table = self.alchemy.get(alchemy_config.identity_table)
        # FIXME: this MAY break
        self._identity_column = self._identity_table.__getattribute__(alchemy_config.identity_column)
        # self._identity_column = self._identity_table.__getattribute__(self._identity_table,
        #                                                               alchemy_config.identity_column)

    @property
    def _identity_chain(self) -> tuple:
        """Find a relationship path starting from the master table and ending at the identity table, and return it."""
        return table_dfs(self._master_table, self._identity_table)

    def interface_factory(self) -> Type[CommandInterface]:
        """Create the :class:`CommandInterface` class for the Serf."""

        # noinspection PyMethodParameters
        class GenericInterface(CommandInterface):
            alchemy: Alchemy = self.alchemy
            bot: "Serf" = self
            loop: AbstractEventLoop = self.loop

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

    def init_sentry(self):
        sentry_dsn = self.get_secret("sentry")
        if sentry_dsn:
            # noinspection PyUnreachableCode
            if __debug__:
                release = f"Dev"
            else:
                release = f"{version}"
            log.debug("Initializing Sentry...")
            sentry_sdk.init(sentry_dsn,
                            integrations=[AioHttpIntegration(),
                                          SqlalchemyIntegration(),
                                          LoggingIntegration(event_level=None)],
                            release=release)
            log.info(f"Sentry: enabled (Royalnet {release})")
        else:
            log.info("Sentry: disabled")

    def get_secret(self, username: str):
        """Get a Royalnet secret from the keyring.

        Args:
            username: the name of the secret that should be retrieved."""
        return get_password(f"Royalnet/{self.secrets_name}", username)

    async def run(self):
        """A coroutine that starts the event loop and handles command calls."""
        raise NotImplementedError()

    def run_blocking(self):
        """Blockingly run the Serf.

        This should be used as the target of a :class:`multiprocessing.Process`."""
        self.init_sentry()
        self.loop.run_until_complete(self.run())
