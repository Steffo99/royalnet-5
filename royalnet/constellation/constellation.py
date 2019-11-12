import typing
import uvicorn
import logging
import sentry_sdk
from sentry_sdk.integrations.aiohttp import AioHttpIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from sentry_sdk.integrations.logging import LoggingIntegration
import royalnet
import keyring
from starlette.applications import Starlette
from .star import PageStar, ExceptionStar


log = logging.getLogger(__name__)


class Constellation:
    """A Constellation is the class that represents the webserver.

    It runs multiple :class:`Star`s, which represent the routes of the website.

    It also handles the :class:`Alchemy` connection, and it _will_ support Herald connections too."""
    def __init__(self,
                 secrets_name: str,
                 database_uri: str,
                 tables: set,
                 page_stars: typing.List[typing.Type[PageStar]] = None,
                 exc_stars: typing.List[typing.Type[ExceptionStar]] = None,
                 *,
                 debug: bool = __debug__,):
        if page_stars is None:
            page_stars = []

        if exc_stars is None:
            exc_stars = []

        self.secrets_name: str = secrets_name

        log.info(f"Creating Starlette in {'Debug' if __debug__ else 'Production'} mode...")
        self.starlette = Starlette(debug=debug)

        log.info(f"Creating Alchemy with Tables: {' '.join([table.__name__ for table in tables])}")
        self.alchemy: royalnet.database.Alchemy = royalnet.database.Alchemy(database_uri=database_uri, tables=tables)

        log.info("Registering PageStars...")
        for SelectedPageStar in page_stars:
            log.info(f"Registering: {page_star_instance.path} -> {page_star_instance.__class__.__name__}")
            try:
                page_star_instance = SelectedPageStar(constellation=self)
            except Exception as e:
                log.error(f"{e.__class__.__qualname__} during the registration of {SelectedPageStar.__qualname__}!")
                raise
            self.starlette.add_route(page_star_instance.path, page_star_instance.page, page_star_instance.methods)

        log.info("Registering ExceptionStars...")
        for SelectedExcStar in exc_stars:
            log.info(f"Registering: {exc_star_instance.error} -> {exc_star_instance.__class__.__name__}")
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

    def run_blocking(self, address: str, port: int):
        """Blockingly run the Constellation.

        This should be used as the target of a :class:`multiprocessing.Process`.

        Args:
            address: The IP address this Constellation should bind to.
            port: The port this Constellation should listen for requests on."""
        # Initialize Sentry on the process
        sentry_dsn = self.get_secret("sentry")
        if sentry_dsn:
            # noinspection PyUnreachableCode
            if __debug__:
                release = "DEV"
            else:
                release = royalnet.version.semantic
            log.info(f"Sentry: enabled (Royalnet {release})")
            sentry_sdk.init(sentry_dsn,
                            integrations=[AioHttpIntegration(),
                                          SqlalchemyIntegration(),
                                          LoggingIntegration(event_level=None)],
                            release=release)
        else:
            log.info("Sentry: disabled")
        # Run the server
        log.info(f"Running constellation server on {address}:{port}...")
        uvicorn.run(self.starlette, host=address, port=port)
