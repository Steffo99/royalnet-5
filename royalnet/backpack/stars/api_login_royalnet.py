import datetime
import royalnet.utils as ru
from royalnet.constellation.api import *
from ..tables.users import User
from ..tables.aliases import Alias
from ..tables.tokens import Token


class ApiLoginRoyalnetStar(ApiStar):
    path = "/api/login/royalnet/v1"

    methods = ["POST"]

    async def api(self, data: ApiData) -> ru.JSON:
        TokenT = self.alchemy.get(Token)
        UserT = self.alchemy.get(User)
        AliasT = self.alchemy.get(Alias)

        username = data["username"]
        password = data["password"]

        async with self.session_acm() as session:
            user: User = await ru.asyncify(session.query(UserT).filter_by(username=username).one_or_none)
            if user is None:
                raise NotFoundError("User not found")
            pswd_check = user.test_password(password)
            if not pswd_check:
                raise ApiError("Invalid password")
            token: Token = TokenT.generate(alchemy=self.alchemy, user=user, expiration_delta=datetime.timedelta(days=7))
            session.add(token)
            await ru.asyncify(session.commit)
            response = token.json()

        return response
