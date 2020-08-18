import datetime
import secrets

import sqlalchemy as s
import sqlalchemy.ext.declarative as sed
import sqlalchemy.orm as so

import royalnet.utils as ru


# noinspection PyAttributeOutsideInit
class Token:
    __tablename__ = "tokens"

    @sed.declared_attr
    def token(self):
        return s.Column(s.String, primary_key=True)

    @sed.declared_attr
    def user_id(self):
        return s.Column(s.Integer, s.ForeignKey("users.uid"), nullable=False)

    @sed.declared_attr
    def user(self):
        return so.relationship("User", backref="tokens")

    @sed.declared_attr
    def expiration(self):
        return s.Column(s.DateTime, nullable=False)

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
