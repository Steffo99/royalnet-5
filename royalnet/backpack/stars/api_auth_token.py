from typing import *
import datetime
import royalnet.utils as ru
from royalnet.constellation.api import *
from ..tables.tokens import Token


class ApiAuthTokenStar(ApiStar):
    path = "/api/auth/token/v1"

    methods = ["GET", "POST"]

    parameters = {
        "get": {},
        "post": {
            "duration": "The duration in seconds of the new token."
        }
    }

    auth = {
        "get": True,
        "post": True,
    }

    tags = ["auth"]

    async def get(self, data: ApiData) -> ru.JSON:
        """Get information about the current login token."""
        token = await data.token()
        return token.json()

    async def post(self, data: ApiData) -> ru.JSON:
        """Create a new login token for the authenticated user.

        Keep it secret, as it is basically a password!"""
        user = await data.user()
        try:
            duration = int(data["duration"])
        except ValueError:
            raise InvalidParameterError("Duration is not a valid integer")
        new_token = Token.generate(self.alchemy, user, datetime.timedelta(seconds=duration))
        data.session.add(new_token)
        await data.session_commit()
        return new_token.json()
