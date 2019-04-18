import typing
import asyncio
import logging
from ..utils import Command, NetworkHandler
from ..commands import NullCommand
from ..network import RoyalnetLink, Message, RequestError, RoyalnetConfig
from ..database import Alchemy, DatabaseConfig, relationshiplinkchain

loop = asyncio.get_event_loop()
log = logging.getLogger(__name__)


class GenericBot:
    def _init_commands(self,
                       commands: typing.List[typing.Type[Command]],
                       missing_command: typing.Type[Command],
                       error_command: typing.Type[Command]):
        log.debug(f"Now generating commands")
        self.commands: typing.Dict[str, typing.Type[Command]] = {}
        self.network_handlers: typing.Dict[typing.Type[Message], typing.Type[NetworkHandler]] = {}
        for command in commands:
            self.commands[f"!{command.command_name}"] = command
            self.network_handlers = {**self.network_handlers, **command.network_handler_dict()}
        self.missing_command: typing.Type[Command] = missing_command
        self.error_command: typing.Type[Command] = error_command
        log.debug(f"Successfully generated commands")

    def _init_royalnet(self, royalnet_config: RoyalnetConfig):
        self.network: RoyalnetLink = RoyalnetLink(royalnet_config.master_uri, royalnet_config.master_secret, "discord",
                                                  self._network_handler)
        log.debug(f"Running RoyalnetLink {self.network}")
        loop.create_task(self.network.run())

    def _network_handler(self, message: Message) -> Message:
            log.debug(f"Received {message} from the RoyalnetLink")
            try:
                network_handler = self.network_handlers[message.__class__]
            except KeyError as exc:
                log.debug(f"Missing network_handler for {message}")
                return RequestError(KeyError("Missing network_handler"))
            try:
                log.debug(f"Using {network_handler} as handler for {message}")
                return await network_handler.discord(message)
            except Exception as exc:
                log.debug(f"Exception {exc} in {network_handler}")
                return RequestError(exc)

    def _init_database(self, commands: typing.List[typing.Type[Command]], database_config: DatabaseConfig):
        required_tables = set()
        for command in commands:
            required_tables = required_tables.union(command.require_alchemy_tables)
        self.alchemy = Alchemy(database_config.database_uri, required_tables)
        self.master_table = self.alchemy.__getattribute__(database_config.master_table.__name__)
        self.identity_table = self.alchemy.__getattribute__(database_config.identity_table.__name__)
        self.identity_column = self.identity_table.__getattribute__(self.identity_table,
                                                                    database_config.identity_column_name)
        self.identity_chain = relationshiplinkchain(self.master_table, self.identity_table)

    def __init__(self, *,
                 royalnet_config: RoyalnetConfig,
                 database_config: typing.Optional[DatabaseConfig] = None,
                 commands: typing.Optional[typing.List[typing.Type[Command]]] = None,
                 missing_command: typing.Type[Command] = NullCommand,
                 error_command: typing.Type[Command] = NullCommand):
        if commands is None:
            commands = []
        self._init_commands(commands, missing_command=missing_command, error_command=error_command)
        self._init_royalnet(royalnet_config=royalnet_config)
        if database_config is None:
            self.alchemy = None
            self.master_table = None
            self.identity_table = None
            self.identity_column = None
        else:
            self._init_database(commands=commands, database_config=database_config)
