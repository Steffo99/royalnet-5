from typing import *
import bcrypt
import royalnet.utils as ru
from sqlalchemy import Column, \
                       Integer, \
                       String, \
                       LargeBinary, \
                       inspect
from sqlalchemy.ext.declarative import declared_attr
from .roles import Role
from .aliases import Alias
from ...utils import JSON, asyncify


# noinspection PyAttributeOutsideInit
class User:
    __tablename__ = "users"

    @declared_attr
    def uid(self):
        return Column(Integer, unique=True, primary_key=True)

    @declared_attr
    def username(self):
        return Column(String, unique=True, nullable=False)

    @declared_attr
    def email(self):
        return Column(String, unique=True)

    @declared_attr
    def password(self):
        return Column(LargeBinary)

    @declared_attr
    def avatar_url(self):
        return Column(String)

    @classmethod
    async def find(cls, alchemy, session, identifier: Union[str, int]):
        if isinstance(identifier, str):
            alias = await ru.asyncify(session.query(alchemy.get(Alias)).filter_by(alias=identifier.lower()).one_or_none)
            if alias is None:
                return None
            else:
                return alias.user
        elif isinstance(identifier, int):
            return await ru.asyncify(session.query(alchemy.get(cls)).get, identifier)
        else:
            raise TypeError("alias is of an invalid type.")

    def json(self) -> JSON:
        return {
            "uid": self.uid,
            "username": self.username,
            "email": self.email,
            "password_set": self.password is not None,
            "avatar_url": self.avatar_url,
            "roles": self.roles,
            "aliases": self.aliases
        }

    def set_password(self, password: str) -> None:
        byte_password: bytes = bytes(password, encoding="UTF8")
        self.password = bcrypt.hashpw(byte_password, bcrypt.gensalt(14))

    def test_password(self, password: str) -> bool:
        if self.password is None:
            raise ValueError("No password is set")
        byte_password: bytes = bytes(password, encoding="UTF8")
        return bcrypt.checkpw(byte_password, self.password)

    @property
    def roles(self) -> list:
        return list(map(lambda a: a.role, self._roles))

    def add_role(self, alchemy, role: str) -> None:
        role = role.lower()
        session = inspect(self).session
        session.add(alchemy.get(Role)(user=self, role=role))

    async def delete_role(self, alchemy, role: str) -> None:
        role = role.lower()
        session = inspect(self).session
        role = await asyncify(session.query(alchemy.get(Role)).filter_by(user=self, role=role).one_or_none)
        if role is not None:
            session.delete(role)

    @property
    def aliases(self) -> list:
        return list(map(lambda a: a.alias, self._aliases))

    def add_alias(self, alchemy, alias: str) -> None:
        alias = alias.lower()
        session = inspect(self).session
        session.add(alchemy.get(Alias)(user=self, alias=alias))

    async def delete_alias(self, alchemy, alias: str) -> None:
        alias = alias.lower()
        session = inspect(self).session
        alias = await asyncify(session.query(alchemy.get(Alias)).filter_by(user=self, alias=alias).one_or_none)
        if alias is not None:
            session.delete(alias)

    def __repr__(self):
        return f"<{self.__class__.__qualname__} {self.username}>"

    def __str__(self):
        return self.username
