from sqlalchemy import Column, \
                       Integer, \
                       String, \
                       LargeBinary
from sqlalchemy.ext.declarative import declared_attr


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

    def __repr__(self):
        return f"<{self.__class__.__qualname__} {self.username}>"

    def __str__(self):
        return self.username
