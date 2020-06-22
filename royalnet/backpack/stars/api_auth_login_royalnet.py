import datetime
import royalnet.utils as ru
from royalnet.constellation.api import *
from royalnet.constellation.api.apierrors import *
from ..tables.users import User
from ..tables.tokens import Token


class ApiAuthLoginRoyalnetStar(ApiStar):
    path = "/api/auth/login/royalnet/v1"

    methods = ["POST"]

    parameters = {
        "post": {
            "username": "The name of the user you are logging in as.",
            "password": "The password of the user you are logging in as.",
        }
    }

    tags = ["auth"]

    async def post(self, data: ApiData) -> ru.JSON:
        """Login with a Royalnet account.

        The method returns a API token valid for 7 days that identifies and authenticates the user to the API.

        Keep it secret, as it is basically a password!
        """
        TokenT = self.alchemy.get(Token)
        UserT = self.alchemy.get(User)

        username = data["username"]
        password = data["password"]

        async with self.session_acm() as session:
            user: User = await ru.asyncify(session.query(UserT).filter_by(username=username).one_or_none)
            if user is None:
                raise NotFoundError("User not found")
            pswd_check = user.test_password(password)
            if not pswd_check:
                raise UnauthorizedError("Invalid password")
            token: Token = TokenT.generate(alchemy=self.alchemy, user=user, expiration_delta=datetime.timedelta(days=7))
            session.add(token)
            await ru.asyncify(session.commit)
            response = token.json()

        return response
