import datetime
import secrets
from sqlalchemy import *
from sqlalchemy.orm import *
from sqlalchemy.ext.declarative import declared_attr
import royalnet.utils as ru


class Token:
    __tablename__ = "tokens"

    @declared_attr
    def token(self):
        return Column(String, primary_key=True)

    @declared_attr
    def user_id(self):
        return Column(Integer, ForeignKey("users.uid"), nullable=False)

    @declared_attr
    def user(self):
        return relationship("User", backref="tokens")

    @declared_attr
    def expiration(self):
        return Column(DateTime, nullable=False)

    @property
    def expired(self):
        return datetime.datetime.now() > self.expiration

    @expired.setter
    def expired(self, value):
        if value is True:
            self.expiration = datetime.datetime.fromtimestamp(0)
        else:
            raise ValueError("'expired' can only be set to True.")

    @classmethod
    def generate(cls, alchemy, user, expiration_delta: datetime.timedelta):
        # noinspection PyArgumentList
        TokenT = alchemy.get(cls)
        token = TokenT(user=user, expiration=datetime.datetime.now() + expiration_delta, token=secrets.token_urlsafe())
        return token

    def json(self) -> dict:
        return {
            "user": self.user.json(),
            "token": self.token,
            "expiration": self.expiration.isoformat()
        }

    @classmethod
    async def find(cls, alchemy, session, token: str) -> "Token":
        return await ru.asyncify(session.query(alchemy.get(cls)).filter_by(token=token).one_or_none)
