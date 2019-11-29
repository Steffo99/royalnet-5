import logging
import importlib
import asyncio as aio
from typing import *
import royalnet.alchemy as ra
import royalnet.herald as rh
import royalnet.utils as ru
import royalnet.commands as rc
from .star import PageStar, ExceptionStar

try:
    import uvicorn
    from starlette.applications import Starlette
except ImportError:
    uvicorn = None
    Starlette = None

try:
    import sentry_sdk
except ImportError:
    sentry_sdk = None
    AioHttpIntegration = None
    SqlalchemyIntegration = None
    LoggingIntegration = None

try:
    import coloredlogs
except ImportError:
    coloredlogs = None


log = logging.getLogger(__name__)

UVICORN_LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": True,
    "formatters": {},
    "handlers": {},
    "loggers": {},
}


class Constellation:
    """The class that represents the webserver.

    It runs multiple :class:`Star`, which represent the routes of the website.

    It also handles the :class:`Alchemy` connection, and Herald connections too."""
    def __init__(self,
                 alchemy_cfg: Dict[str, Any],
                 herald_cfg: Dict[str, Any],
                 packs_cfg: Dict[str, Any],
                 constellation_cfg: Dict[str, Any],
                 **_):
        if Starlette is None:
            raise ImportError("`constellation` extra is not installed")

        # Import packs
        pack_names = packs_cfg["active"]
        packs = {}
        for pack_name in pack_names:
            log.debug(f"Importing pack: {pack_name}")
            try:
                packs[pack_name] = importlib.import_module(pack_name)
            except ImportError as e:
                log.error(f"Error during the import of {pack_name}: {e}")
        log.info(f"Packs: {len(packs)} imported")

        self.alchemy = None
        """The :class:`~ra.Alchemy` of this Constellation."""

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
                    tables = tables.union(pack.available_tables)
                except AttributeError:
                    log.warning(f"Pack `{pack}` does not have the `available_tables` attribute.")
                    continue
            # Create the Alchemy
            self.alchemy = ra.Alchemy(alchemy_cfg["database_url"], tables)
            log.info(f"Alchemy: {self.alchemy}")

        # Herald
        self.herald: Optional[rh.Link] = None
        """The :class:`Link` object connecting the :class:`Constellation` to the rest of the herald network."""

        self.herald_task: Optional[aio.Task] = None
        """A reference to the :class:`aio.Task` that runs the :class:`rh.Link`."""

        self.Interface: Type[rc.CommandInterface] = self.interface_factory()
        """The :class:`~rc.CommandInterface` class of this :class:`Constellation`."""

        self.events: Dict[str, rc.Event] = {}
        """A dictionary containing all :class:`~rc.Event` that can be handled by this :class:`Constellation`."""

        self.starlette = Starlette(debug=__debug__)
        """The :class:`~starlette.Starlette` app."""

        # Register Events
        for pack_name in packs:
            pack = packs[pack_name]
            pack_cfg = packs_cfg.get(pack_name, {})
            try:
                events = pack.available_events
            except AttributeError:
                log.warning(f"Pack `{pack}` does not have the `available_events` attribute.")
            else:
                self.register_events(events, pack_cfg)
        log.info(f"Events: {len(self.events)} events")

        if rh.Link is None:
            log.info("Herald: not installed")
        elif not herald_cfg["enabled"]:
            log.info("Herald: disabled")
        else:
            self.init_herald(herald_cfg)
            log.info(f"Herald: enabled")

        # Register PageStars and ExceptionStars
        for pack_name in packs:
            pack = packs[pack_name]
            pack_cfg = packs_cfg.get(pack_name, {})
            try:
                page_stars = pack.available_page_stars
            except AttributeError:
                log.warning(f"Pack `{pack}` does not have the `available_page_stars` attribute.")
            else:
                self.register_page_stars(page_stars, pack_cfg)
            try:
                exc_stars = pack.available_exception_stars
            except AttributeError:
                log.warning(f"Pack `{pack}` does not have the `available_exception_stars` attribute.")
            else:
                self.register_exc_stars(exc_stars, pack_cfg)
        log.info(f"PageStars: {len(self.starlette.routes)} stars")
        log.info(f"ExceptionStars: {len(self.starlette.exception_handlers)} stars")

        self.running: bool = False
        """Is the :class:`Constellation` server currently running?"""

        self.address: str = constellation_cfg["address"]
        """The address that the :class:`Constellation` will bind to when run."""

        self.port: int = constellation_cfg["port"]
        """The port on which the :class:`Constellation` will listen for connection on."""

    # TODO: is this a good idea?
    def interface_factory(self) -> Type[rc.CommandInterface]:
        """Create the :class:`rc.CommandInterface` class for the :class:`Constellation`."""

        # noinspection PyMethodParameters
        class GenericInterface(rc.CommandInterface):
            alchemy: ra.Alchemy = self.alchemy
            constellation = self

            async def call_herald_event(ci, destination: str, event_name: str, **kwargs) -> Dict:
                """Send a :class:`rh.Request` to a specific destination, and wait for a
                :class:`rh.Response`."""
                if self.herald is None:
                    raise rc.UnsupportedError("`royalherald` is not enabled on this Constellation.")
                request: rh.Request = rh.Request(handler=event_name, data=kwargs)
                response: rh.Response = await self.herald.request(destination=destination, request=request)
                if isinstance(response, rh.ResponseFailure):
                    if response.name == "no_event":
                        raise rc.CommandError(f"There is no event named {event_name} in {destination}.")
                    elif response.name == "exception_in_event":
                        # TODO: pretty sure there's a better way to do this
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
                            raise TypeError(f"Herald action call returned invalid error:\n"
                                            f"[p]{response}[/p]")
                elif isinstance(response, rh.ResponseSuccess):
                    return response.data
                else:
                    raise TypeError(f"Other Herald Link returned unknown response:\n"
                                    f"[p]{response}[/p]")

        return GenericInterface

    def init_herald(self, herald_cfg: Dict[str, Any]):
        """Create a :class:`rh.Link`."""
        herald_cfg["name"] = "constellation"
        self.herald: rh.Link = rh.Link(rh.Config.from_config(**herald_cfg), self.network_handler)

    async def network_handler(self, message: Union[rh.Request, rh.Broadcast]) -> rh.Response:
        try:
            event: rc.Event = self.events[message.handler]
        except KeyError:
            log.warning(f"No event for '{message.handler}'")
            return rh.ResponseFailure("no_event", f"This serf does not have any event for {message.handler}.")
        log.debug(f"Event called: {event.name}")
        if isinstance(message, rh.Request):
            try:
                response_data = await event.run(**message.data)
                return rh.ResponseSuccess(data=response_data)
            except Exception as e:
                ru.sentry_exc(e)
                return rh.ResponseFailure("exception_in_event",
                                          f"An exception was raised in the event for '{message.handler}'.",
                                          extra_info={
                                              "type": e.__class__.__qualname__,
                                              "message": str(e)
                                          })
        elif isinstance(message, rh.Broadcast):
            await event.run(**message.data)

    def register_events(self, events: List[Type[rc.Event]], pack_cfg: Dict[str, Any]):
        for SelectedEvent in events:
            # Create a new interface
            interface = self.Interface(config=pack_cfg)
            # Initialize the event
            try:
                event = SelectedEvent(interface)
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

    def register_page_stars(self, page_stars: List[Type[PageStar]], pack_cfg: Dict[str, Any]):
        for SelectedPageStar in page_stars:
            log.debug(f"Registering: {SelectedPageStar.path} -> {SelectedPageStar.__qualname__}")
            try:
                page_star_instance = SelectedPageStar(constellation=self, config=pack_cfg)
            except Exception as e:
                log.error(f"Skipping: "
                          f"{SelectedPageStar.__qualname__} - {e.__class__.__qualname__} in the initialization.")
                ru.sentry_exc(e)
                continue
            self.starlette.add_route(page_star_instance.path, page_star_instance.page, page_star_instance.methods)

    def register_exc_stars(self, exc_stars: List[Type[ExceptionStar]], pack_cfg: Dict[str, Any]):
        for SelectedPageStar in exc_stars:
            log.debug(f"Registering: {SelectedPageStar.error} -> {SelectedPageStar.__qualname__}")
            try:
                page_star_instance = SelectedPageStar(constellation=self, config=pack_cfg)
            except Exception as e:
                log.error(f"Skipping: "
                          f"{SelectedPageStar.__qualname__} - {e.__class__.__qualname__} in the initialization.")
                ru.sentry_exc(e)
                continue
            self.starlette.add_exception_handler(page_star_instance.error, page_star_instance.page)

    def run_blocking(self):
        log.info(f"Running Constellation on https://{self.address}:{self.port}/...")
        loop: aio.AbstractEventLoop = aio.get_event_loop()
        self.running = True
        # TODO: figure out how to run the correct event loop
        # loop.create_task(self.herald.run())
        try:
            uvicorn.run(self.starlette, host=self.address, port=self.port, log_config=UVICORN_LOGGING_CONFIG)
        finally:
            self.running = False

    @classmethod
    def run_process(cls,
                    alchemy_cfg: Dict[str, Any],
                    herald_cfg: Dict[str, Any],
                    sentry_cfg: Dict[str, Any],
                    packs_cfg: Dict[str, Any],
                    constellation_cfg: Dict[str, Any],
                    logging_cfg: Dict[str, Any]):
        """Blockingly create and run the Constellation.

        This should be used as the target of a :class:`multiprocessing.Process`."""
        ru.init_logging(logging_cfg)

        if sentry_cfg is None or not sentry_cfg["enabled"]:
            log.info("Sentry: disabled")
        else:
            try:
                ru.init_sentry(sentry_cfg)
            except ImportError:
                log.info("Sentry: not installed")

        constellation = cls(alchemy_cfg=alchemy_cfg,
                            herald_cfg=herald_cfg,
                            packs_cfg=packs_cfg,
                            constellation_cfg=constellation_cfg)

        # Run the server
        constellation.run_blocking()

    def __repr__(self):
        return f"<{self.__class__.__qualname__}: {'running' if self.running else 'inactive'}>"
