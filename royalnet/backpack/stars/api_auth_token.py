from typing import *
import datetime
import royalnet.utils as ru
import royalnet.constellation.api as rca
from ..tables.tokens import Token


class ApiAuthTokenStar(rca.ApiStar):
    path = "/api/auth/token/v1"

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

    @rca.magic
    async def get(self, data: rca.ApiData) -> ru.JSON:
        """Get information about the current login token."""
        token = await data.token()
        return token.json()

    @rca.magic
    async def post(self, data: rca.ApiData) -> ru.JSON:
        """Create a new login token for the authenticated user.

        Keep it secret, as it is basically a password!"""
        user = await data.user()
        try:
            duration = int(data["duration"])
        except ValueError:
            raise rca.InvalidParameterError("Duration is not a valid integer")
        new_token = Token.generate(self.alchemy, user, datetime.timedelta(seconds=duration))
        data.session.add(new_token)
        await data.session_commit()
        return new_token.json()
