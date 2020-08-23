import abc
import asyncio as aio
import importlib
import logging
import sys
import traceback
from typing import *

from sqlalchemy.schema import Table

import royalnet.alchemy as ra
import royalnet.backpack.tables as rbt
import royalnet.commands as rc
import royalnet.herald as rh
import royalnet.utils as ru

log = logging.getLogger(__name__)


class Serf(abc.ABC):
    """An abstract class, to be used as base to implement Royalnet bots on multiple interfaces (such as Telegram or
    Discord)."""
    interface_name = NotImplemented
    prefix = NotImplemented

    _master_table: type = rbt.User
    _identity_table: type = NotImplemented
    _identity_column: str = NotImplemented

    def __init__(self,
                 loop: aio.AbstractEventLoop,
                 alchemy_cfg: rc.ConfigDict,
                 herald_cfg: rc.ConfigDict,
                 packs_cfg: rc.ConfigDict,
                 **_):
        self.loop: Optional[aio.AbstractEventLoop] = loop
        """The event loop this Serf is running on."""

        self.tasks: Optional[ru.TaskList] = ru.TaskList(self.loop)
        """A list of all running tasks of the serf. Initialized at the serf start."""

        # Import packs
        pack_names = packs_cfg["active"]
        packs = {}
        for pack_name in pack_names:
            log.debug(f"Importing pack: {pack_name}")
            try:
                packs[pack_name] = {
                    "commands": importlib.import_module(f".commands", pack_name),
                    "events": importlib.import_module(f".events", pack_name),
                    "stars": importlib.import_module(f".stars", pack_name),
                    "tables": importlib.import_module(f".tables", pack_name),
                }
            except ImportError as e:
                log.error(f"{e.__class__.__name__} during the import of {pack_name}:\n"
                          f"{''.join(traceback.format_exception(*sys.exc_info()))}")
        log.info(f"Packs: {len(packs)} imported")

        self.alchemy: Optional[ra.Alchemy] = None
        """The :class:`Alchemy` object connecting this :class:`Serf` to a database."""

        self.master_table: Optional[Table] = None
        """The central table listing all users. It usually is :class:`User`."""

        self.identity_table: Optional[Table] = None
        """The identity table containing the interface data (such as the Telegram user data) and that is in a 
        many-to-one relationship with the master table."""

        self.identity_column: Optional[str] = None
        """The name of the column in the identity table that contains a unique user identifier. (???)"""

        # Alchemy
        if ra.Alchemy is None:
            log.info("Alchemy: not installed")
        elif not alchemy_cfg["enabled"]:
            log.info("Alchemy: disabled")
        else:
            # Find all tables
            tables = set()
            for pack in packs.values():
                try:
                    # noinspection PyUnresolvedReferences
                    tables = tables.union(pack["tables"].available_tables)
                except AttributeError:
                    log.warning(f"Pack `{pack}` does not have the `available_tables` attribute.")
                    continue
            # Create the Alchemy
            self.init_alchemy(alchemy_cfg, tables)
            log.info(f"Alchemy: {self.alchemy}")

        self.herald: Optional[rh.Link] = None
        """The :class:`Link` object connecting the :class:`Serf` to the rest of the Herald network."""

        self.herald_task: Optional[aio.Task] = None
        """A reference to the :class:`asyncio.Task` that runs the :class:`Link`."""

        self.events: Dict[str, rc.HeraldEvent] = {}
        """A dictionary containing all :class:`Event` that can be handled by this :class:`Serf`."""

        self.commands: Dict[str, rc.Command] = {}
        """The :class:`dict` connecting each command name to its :class:`Command` object."""

        for pack_name in packs:
            pack = packs[pack_name]
            pack_cfg = packs_cfg.get(pack_name, {})
            try:
                # noinspection PyUnresolvedReferences
                events = pack["events"].available_events
            except AttributeError:
                log.warning(f"Pack `{pack}` does not have the `available_events` attribute.")
            else:
                self.register_events(events, pack_cfg)
            try:
                # noinspection PyUnresolvedReferences
                commands = pack["commands"].available_commands
            except AttributeError:
                log.warning(f"Pack `{pack}` does not have the `available_commands` attribute.")
            else:
                self.register_commands(commands, pack_cfg)
        log.info(f"Events: {len(self.events)} events")
        log.info(f"Commands: {len(self.commands)} commands")

        if rh.Link is None:
            log.info("Herald: not installed")
        elif not herald_cfg["enabled"]:
            log.info("Herald: disabled")
        else:
            self.init_herald(herald_cfg)
            log.info(f"Herald: enabled")

    def init_alchemy(self, alchemy_cfg: Dict[str, Any], tables: Set[type]) -> None:
        """Create and initialize the :class:`Alchemy` with the required tables, and find the link between the master
        table and the identity table."""
        self.alchemy = ra.Alchemy(alchemy_cfg["database_url"], tables)

    @property
    def identity_chain(self) -> tuple:
        """Find a relationship path starting from the master table and ending at the identity table, and return it."""
        return ra.table_dfs(self.master_table, self.identity_table)

    async def call_herald_event(self, destination: str, event_name: str, **kwargs) -> Dict:
        """Send a :class:`royalherald.Request` to a specific destination, and wait for a
        :class:`royalherald.Response`."""
        if self.herald is None:
            raise rc.UnsupportedError("`royalherald` is not enabled on this serf.")
        request: rh.Request = rh.Request(handler=event_name, data=kwargs)
        response: rh.Response = await self.herald.request(destination=destination, request=request)
        if isinstance(response, rh.ResponseFailure):
            if response.name == "no_event":
                raise rc.ProgramError(f"There is no event named {event_name} in {destination}.")
            elif response.name == "error_in_event":
                if response.extra_info["type"] == "CommandError":
                    raise rc.CommandError(response.extra_info["message"])
                elif response.extra_info["type"] == "UserError":
                    raise rc.UserError(response.extra_info["message"])
                elif response.extra_info["type"] == "InvalidInputError":
                    raise rc.InvalidInputError(response.extra_info["message"])
                elif response.extra_info["type"] == "UnsupportedError":
                    raise rc.UnsupportedError(response.extra_info["message"])
                elif response.extra_info["type"] == "ConfigurationError":
                    raise rc.ConfigurationError(response.extra_info["message"])
                elif response.extra_info["type"] == "ExternalError":
                    raise rc.ExternalError(response.extra_info["message"])
                else:
                    raise rc.ProgramError(f"Invalid error in Herald event '{event_name}':\n"
                                          f"[b]{response.extra_info['type']}[/b]\n"
                                          f"{response.extra_info['message']}")
            elif response.name == "unhandled_exception_in_event":
                raise rc.ProgramError(f"Unhandled exception in Herald event '{event_name}':\n"
                                      f"[b]{response.extra_info['type']}[/b]\n"
                                      f"{response.extra_info['message']}")
            else:
                raise rc.ProgramError(f"Unknown response in Herald event '{event_name}':\n"
                                      f"[b]{response.name}[/b]"
                                      f"[p]{response}[/p]")
        elif isinstance(response, rh.ResponseSuccess):
            return response.data
        else:
            raise rc.ProgramError(f"Other Herald Link returned unknown response:\n"
                                  f"[p]{response}[/p]")

    def register_commands(self, commands: List[Type[rc.Command]], pack_cfg: rc.ConfigDict) -> None:
        """Initialize and register all commands passed as argument."""
        # Instantiate the Commands
        for SelectedCommand in commands:
            # Try to instantiate the command
            try:
                command = SelectedCommand(serf=self, config=pack_cfg)
            except Exception as e:
                log.error(f"Skipping: "
                          f"{SelectedCommand.__qualname__} - {e.__class__.__qualname__} in the initialization.")
                ru.sentry_exc(e)
                continue
            # Warn if the command would be overriding something
            if SelectedCommand.name in self.commands:
                log.info(f"Overriding (already defined): "
                         f"{SelectedCommand.__qualname__} -> {SelectedCommand.name}")
            else:
                log.debug(f"Registering: "
                          f"{SelectedCommand.__qualname__} -> {SelectedCommand.name}")
            # Register the command in the commands dict
            self.commands[SelectedCommand.name] = command
            # Register aliases, but don't override anything
            for alias in SelectedCommand.aliases:
                if alias not in self.commands:
                    log.debug(f"Aliasing: {SelectedCommand.__qualname__} -> {alias}")
                    self.commands[alias] = self.commands[SelectedCommand.name]
                else:
                    log.warning(f"Ignoring (already defined): {SelectedCommand.__qualname__} -> {alias}")

    def init_herald(self, herald_cfg: rc.ConfigDict):
        """Create a :class:`Link` and bind :class:`Event`."""
        herald_cfg["name"] = self.interface_name
        self.herald: rh.Link = rh.Link(rh.Config.from_config(**herald_cfg), self.network_handler)

    def register_events(self, events: List[Type[rc.HeraldEvent]], pack_cfg: rc.ConfigDict):
        for SelectedEvent in events:
            # Initialize the event
            try:
                event = SelectedEvent(parent=self, config=pack_cfg)
            except Exception as e:
                log.error(f"Skipping: "
                          f"{SelectedEvent.__qualname__} - {e.__class__.__qualname__} in the initialization.")
                ru.sentry_exc(e)
                continue
            # Register the event
            if SelectedEvent.name in self.events:
                log.warning(f"Overriding (already defined): {SelectedEvent.__qualname__} -> {SelectedEvent.name}")
            else:
                log.debug(f"Registering: {SelectedEvent.__qualname__} -> {SelectedEvent.name}")
            self.events[SelectedEvent.name] = event

    async def network_handler(self, message: Union[rh.Request, rh.Broadcast]) -> rh.Response:
        try:
            event: rc.HeraldEvent = self.events[message.handler]
        except KeyError:
            log.warning(f"No event for '{message.handler}'")
            return rh.ResponseFailure("no_event", f"This serf does not have any event for {message.handler}.")
        log.debug(f"Event called: {event.name}")
        if isinstance(message, rh.Request):
            try:
                response_data = await event.run(**message.data)
                return rh.ResponseSuccess(data=response_data)
            except rc.CommandError as e:
                return rh.ResponseFailure("error_in_event",
                                          f"The event '{message.handler}' raised a {e.__class__.__qualname__}.",
                                          extra_info={
                                              "type": e.__class__.__qualname__,
                                              "message": str(e)
                                          })
            except Exception as e:
                ru.sentry_exc(e)
                return rh.ResponseFailure("unhandled_exception_in_event",
                                          f"The event '{message.handler}' raised an unhandled"
                                          f" {e.__class__.__qualname__}.",
                                          extra_info={
                                              "type": e.__class__.__qualname__,
                                              "message": str(e)
                                          })
        elif isinstance(message, rh.Broadcast):
            await event.run(**message.data)

    async def call(self, command: rc.Command, data: rc.CommandData, parameters: List[str]):
        log.info(f"Calling command: {command.name}")
        try:
            # Run the command
            await command.run(rc.CommandArgs(parameters), data)
        except rc.InvalidInputError as e:
            await data.reply(f"⚠️ {e.message}\n"
                             f"Syntax: [c]{self.prefix}{command.name} {command.syntax}[/c]")
        except rc.UserError as e:
            await data.reply(f"⚠️ {e.message}")
        except rc.UnsupportedError as e:
            await data.reply(f"⚠️ {e.message}")
        except rc.ExternalError as e:
            await data.reply(f"⚠️ {e.message}")
        except rc.ConfigurationError as e:
            await data.reply(f"⚠️ {e.message}")
        except rc.ProgramError as e:
            await data.reply(f"⛔️ {e.message}")
        except rc.CommandError as e:
            await data.reply(f"⚠️ {e.message}")
        except Exception as e:
            ru.sentry_exc(e)
            await data.reply(f"⛔️ [b]{e.__class__.__name__}[/b]\n" + '\n'.join(map(lambda a: repr(a), e.args)))

    @staticmethod
    async def press(key: rc.KeyboardKey, data: rc.CommandData):
        log.info(f"Calling key_callback: {repr(key)}")
        try:
            await key.press(data)
        except rc.InvalidInputError as e:
            await data.reply(f"⚠️ {e.message}")
        except rc.UserError as e:
            await data.reply(f"⚠️ {e.message}")
        except rc.UnsupportedError as e:
            await data.reply(f"⚠️ {e.message}")
        except rc.ExternalError as e:
            await data.reply(f"⚠️ {e.message}")
        except rc.ConfigurationError as e:
            await data.reply(f"⚠️ {e.message}")
        except rc.ProgramError as e:
            await data.reply(f"⛔️ {e.message}")
        except rc.CommandError as e:
            await data.reply(f"⚠️ {e.message}")
        except Exception as e:
            ru.sentry_exc(e)
            await data.reply(f"⛔️ [b]{e.__class__.__name__}[/b]\n" + '\n'.join(map(lambda a: repr(a), e.args)))

    async def run(self):
        """A coroutine that starts the event loop and handles command calls."""
        self.herald_task = self.tasks.add(self.herald.run())
        # OVERRIDE THIS METHOD!

    @classmethod
    def run_process(cls, **kwargs):
        """Blockingly create and run the Serf.

        This should be used as the target of a :class:`multiprocessing.Process`."""
        ru.init_logging(kwargs["logging_cfg"])

        if kwargs["sentry_cfg"] is None or not kwargs["sentry_cfg"]["enabled"]:
            log.info("Sentry: disabled")
        else:
            try:
                ru.init_sentry(kwargs["sentry_cfg"])
            except ImportError:
                log.info("Sentry: not installed")

        loop = aio.get_event_loop()

        serf = cls(loop=loop, **kwargs)

        try:
            serf.loop.run_until_complete(serf.run())
        except Exception as e:
            ru.sentry_exc(e, level="fatal")
