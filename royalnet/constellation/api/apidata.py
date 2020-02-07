from .apierrors import MissingParameterError
from royalnet.backpack.tables.tokens import Token
from royalnet.backpack.tables.users import User
from .apierrors import *


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

    async def user(self) -> Token:
        return (await self.token()).user

    @property
    def session(self):
        if self._session is None:
            if self.star.alchemy is None:
                raise UnsupportedError("'alchemy' is not enabled on this Royalnet instance")
            self._session = self.star.alchemy.Session()
        return self._session
