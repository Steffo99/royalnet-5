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

        log.info("Creating starlette app...")
        self.starlette = Starlette(debug=debug)

        log.info(f"Creating alchemy with tables: {' '.join([table.__name__ for table in tables])}")
        self.alchemy: royalnet.database.Alchemy = royalnet.database.Alchemy(database_uri=database_uri, tables=tables)

        log.info("Registering page_stars...")
        for SelectedPageStar in page_stars:
            try:
                page_star_instance = SelectedPageStar(constellation=self)
            except Exception as e:
                log.error(f"{e.__class__.__qualname__} during the registration of {SelectedPageStar.__qualname__}")
                sentry_sdk.capture_exception(e)
                continue
            log.info(f"Registering: {page_star_instance.path} -> {page_star_instance.__class__.__name__}")
            self.starlette.add_route(page_star_instance.path, page_star_instance.page, page_star_instance.methods)

        log.info("Registering exc_stars...")
        for SelectedExcStar in exc_stars:
            try:
                exc_star_instance = SelectedExcStar(constellation=self)
            except Exception as e:
                log.error(f"{e.__class__.__qualname__} during the registration of {SelectedExcStar.__qualname__}")
                sentry_sdk.capture_exception(e)
                continue
            log.info(f"Registering: {exc_star_instance.error} -> {exc_star_instance.__class__.__name__}")
            self.starlette.add_exception_handler(exc_star_instance.error, exc_star_instance.page)

    def _init_sentry(self):
        sentry_dsn = self.get_secret("sentry")
        if sentry_dsn:
            # noinspection PyUnreachableCode
            if __debug__:
                release = "DEV"
            else:
                release = royalnet.version.semantic
            log.info(f"Sentry: enabled (Royalnet {release})")
            self.sentry = sentry_sdk.init(sentry_dsn,
                                          integrations=[AioHttpIntegration(),
                                                        SqlalchemyIntegration(),
                                                        LoggingIntegration(event_level=None)],
                                          release=release)
        else:
            log.info("Sentry: disabled")

    def get_secret(self, username: str):
        return keyring.get_password(f"Royalnet/{self.secrets_name}", username)

    def set_secret(self, username: str, password: str):
        return keyring.set_password(f"Royalnet/{self.secrets_name}", username, password)

    def run_blocking(self, address: str, port: int, verbose: bool):
        if verbose:
            core_logger = logging.root
            core_logger.setLevel(logging.DEBUG)
            stream_handler = logging.StreamHandler()
            stream_handler.formatter = logging.Formatter("{asctime}\t{name}\t{levelname}\t{message}", style="{")
            core_logger.addHandler(stream_handler)
            core_logger.debug("Logging setup complete.")
        self._init_sentry()
        log.info(f"Running constellation server on {address}:{port}...")
        uvicorn.run(self.starlette, host=address, port=port)
