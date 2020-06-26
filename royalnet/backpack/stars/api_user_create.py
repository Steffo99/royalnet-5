from typing import *
import datetime
import royalnet.constellation.api as rca
import royalnet.utils as ru
import royalnet.backpack.tables as rbt
from ..tables import *


class ApiUserCreateStar(rca.ApiStar):
    path = "/api/user/create/v1"

    parameters = {
        "post": {
            "username": "The name of the user you are creating.",
            "password": "The password of the user you are creating.",
            "email": "(Optional) The email of the user you are creating.",
            "avatar_url": "(Optional) An URL pointing to the avatar of the user you are creating.",
        }
    }

    tags = ["user"]

    async def post(self, data: rca.ApiData) -> ru.JSON:
        """Create a new Royalnet account."""
        UserT = self.alchemy.get(User)

        username = data.str("username")
        password = data.str("password")
        email = data.str("email", optional=True)
        avatar_url = data.str("avatar_url", optional=True)

        # Check if the username is used by an user or an alias
        user = await User.find(self.alchemy, data.session, username)
        if user is not None:
            raise rca.InvalidParameterError("An user with that username or alias already exists.")

        # Create the user
        user = UserT(
            username=username,
            email=email,
            avatar_url=avatar_url
        )
        data.session.add(user)
        user.set_password(password)
        user.add_alias(self.alchemy, username)
        await data.session_commit()

        return user.json()
