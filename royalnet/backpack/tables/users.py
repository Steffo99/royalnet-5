import bcrypt
from sqlalchemy import Column, \
                       Integer, \
                       String, \
                       LargeBinary
from sqlalchemy.ext.declarative import declared_attr


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
    def password(self):
        return Column(LargeBinary)

    @declared_attr
    def role(self):
        return Column(String, nullable=False)

    @declared_attr
    def avatar(self):
        return Column(LargeBinary)

    def json(self):
        return {
            "uid": self.uid,
            "username": self.username,
            "role": self.role,
            "avatar": self.avatar
        }

    def set_password(self, password: str):
        byte_password: bytes = bytes(password, encoding="UTF8")
        self.password = bcrypt.hashpw(byte_password, bcrypt.gensalt(14))

    def test_password(self, password: str):
        if self.password is None:
            raise ValueError("No password is set")
        byte_password: bytes = bytes(password, encoding="UTF8")
        return bcrypt.checkpw(byte_password, self.password)

    def __repr__(self):
        return f"<{self.__class__.__qualname__} {self.username}>"

    def __str__(self):
        return self.username
