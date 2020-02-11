import logging
from .apierrors import MissingParameterError
from royalnet.backpack.tables.tokens import Token
from royalnet.backpack.tables.users import User
from .apierrors import *
import royalnet.utils as ru

log = logging.getLogger(__name__)


class ApiData(dict):
    def __init__(self, data, star):
        super().__init__(data)
        self.star = star
        self._session = None

    def __missing__(self, key):
        raise MissingParameterError(f"Missing '{key}'")

    async def token(self) -> Token:
        token = await Token.authenticate(self.star.alchemy, self.session, self["token"])
        if token is None:
            raise ForbiddenError("'token' is invalid")
        return token

    async def user(self) -> User:
        return (await self.token()).user

    @property
    def session(self):
        if self._session is None:
            if self.star.alchemy is None:
                raise UnsupportedError("'alchemy' is not enabled on this Royalnet instance")
            log.debug("Creating Session...")
            self._session = self.star.alchemy.Session()
        return self._session

    async def session_commit(self):
        """Asyncronously commit the :attr:`.session` of this object."""
        if self._session:
            log.warning("Session had to be created to be committed")
        # noinspection PyUnresolvedReferences
        log.debug("Committing Session...")
        await ru.asyncify(self.session.commit)

    async def session_close(self):
        """Asyncronously close the :attr:`.session` of this object."""
        if self._session is not None:
            log.debug("Closing Session...")
            await ru.asyncify(self._session.close)
