from typing import *
import datetime
import royalnet.utils as ru
import royalnet.constellation.api as rca
from sqlalchemy import and_
from ..tables.tokens import Token


class ApiUserPasswd(rca.ApiStar):
    path = "/api/user/passwd/v1"

    tags = ["user"]

    parameters = {
        "put": {
            "new_password": "The password you want to set."
        }
    }

    auth = {
        "put": True
    }

    requires_auth = True

    @rca.magic
    async def put(self, data: rca.ApiData) -> ru.JSON:
        """Change the password of the currently logged in user.

        This method also revokes all the issued tokens for the user."""
        TokenT = self.alchemy.get(Token)
        token = await data.token()
        user = token.user
        user.set_password(data["new_password"])
        tokens: List[Token] = await ru.asyncify(
            data.session
                .query(self.alchemy.get(Token))
                .filter(
                    and_(
                        TokenT.user == user,
                        TokenT.expiration >= datetime.datetime.now()
                    ))
                .all
        )
        for t in tokens:
            if t.token != token.token:
                t.expired = True
        await data.session_commit()
        return {
            "revoked_tokens": len(tokens) - 1
        }
