import typing
import logging
import royalnet
import keyring
from .star import PageStar, ExceptionStar

try:
    import uvicorn
    from starlette.applications import Starlette
except ImportError:
    uvicorn = None
    Starlette = None

try:
    import sentry_sdk
    from sentry_sdk.integrations.aiohttp import AioHttpIntegration
    from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
    from sentry_sdk.integrations.logging import LoggingIntegration
except ImportError:
    sentry_sdk = None
    AioHttpIntegration = None
    SqlalchemyIntegration = None
    LoggingIntegration = None


log = logging.getLogger(__name__)


class Constellation:
    """A Constellation is the class that represents the webserver.

    It runs multiple :class:`Star`s, which represent the routes of the website.

    It also handles the :class:`Alchemy` connection, and it _will_ support Herald connections too."""
    def __init__(self,
                 secrets_name: str,
                 database_uri: str,
                 page_stars: typing.List[typing.Type[PageStar]] = None,
                 exc_stars: typing.List[typing.Type[ExceptionStar]] = None,
                 *,
                 debug: bool = __debug__,):
        if Starlette is None:
            raise ImportError("'constellation' extra is not installed")

        if page_stars is None:
            page_stars = []

        if exc_stars is None:
            exc_stars = []

        self.secrets_name: str = secrets_name
        """The secrets_name this Constellation is currently using."""

        self.running: bool = False
        """Is the Constellation currently running?"""

        log.info(f"Creating Starlette in {'Debug' if __debug__ else 'Production'} mode...")
        self.starlette = Starlette(debug=debug)
        """The :class:`Starlette` app."""

        log.debug("Finding required Tables...")
        tables = set(royalnet.backpack.available_tables)
        for SelectedPageStar in page_stars:
            tables = tables.union(SelectedPageStar.tables)
        for SelectedExcStar in exc_stars:
            tables = tables.union(SelectedExcStar.tables)
        log.debug(f"Found Tables: {' '.join([table.__name__ for table in tables])}")

        log.info(f"Creating Alchemy...")
        self.alchemy: royalnet.alchemy.Alchemy = royalnet.alchemy.Alchemy(database_uri=database_uri, tables=tables)
        """The :class:`Alchemy: of this Constellation."""

        log.info("Registering PageStars...")
        for SelectedPageStar in page_stars:
            log.info(f"Registering: {SelectedPageStar.path} -> {SelectedPageStar.__class__.__name__}")
            try:
                page_star_instance = SelectedPageStar(constellation=self)
            except Exception as e:
                log.error(f"{e.__class__.__qualname__} during the registration of {SelectedPageStar.__qualname__}!")
                raise
            self.starlette.add_route(page_star_instance.path, page_star_instance.page, page_star_instance.methods)

        log.info("Registering ExceptionStars...")
        for SelectedExcStar in exc_stars:
            log.info(f"Registering: {SelectedExcStar.error} -> {SelectedExcStar.__class__.__name__}")
            try:
                exc_star_instance = SelectedExcStar(constellation=self)
            except Exception as e:
                log.error(f"{e.__class__.__qualname__} during the registration of {SelectedExcStar.__qualname__}!")
                raise
            self.starlette.add_exception_handler(exc_star_instance.error, exc_star_instance.page)

    def get_secret(self, username: str) -> typing.Optional[str]:
        """Get a Royalnet secret from the keyring.

        Args:
            username: the name of the secret that should be retrieved."""
        return keyring.get_password(f"Royalnet/{self.secrets_name}", username)

    @classmethod
    def run_process(cls,
                    address: str,
                    port: int,
                    secrets_name: str,
                    database_uri: str,
                    page_stars: typing.List[typing.Type[PageStar]] = None,
                    exc_stars: typing.List[typing.Type[ExceptionStar]] = None,
                    *,
                    debug: bool = __debug__,):
        """Blockingly create and run the Constellation.

        This should be used as the target of a :class:`multiprocessing.Process`.

        Args:
            address: The IP address this Constellation should bind to.
            port: The port this Constellation should listen for requests on."""
        constellation = cls(secrets_name=secrets_name,
                            database_uri=database_uri,
                            page_stars=page_stars,
                            exc_stars=exc_stars,
                            debug=debug)

        # Initialize Sentry on the process
        if sentry_sdk is None:
            log.info("Sentry: not installed")
        else:
            sentry_dsn = constellation.get_secret("sentry")
            if not sentry_dsn:
                log.info("Sentry: disabled")
            else:
                # noinspection PyUnreachableCode
                if __debug__:
                    release = f"Dev"
                else:
                    release = f"{royalnet.__version__}"
                log.debug("Initializing Sentry...")
                sentry_sdk.init(sentry_dsn,
                                integrations=[AioHttpIntegration(),
                                              SqlalchemyIntegration(),
                                              LoggingIntegration(event_level=None)],
                                release=release)
                log.info(f"Sentry: enabled (Royalnet {release})")
        # Run the server
        log.info(f"Running Constellation on {address}:{port}...")
        constellation.running = True
        try:
            uvicorn.run(constellation.starlette, host=address, port=port)
        finally:
            constellation.running = False

    def __repr__(self):
        return f"<{self.__class__.__qualname__}: {'running' if self.running else 'inactive'}>"
