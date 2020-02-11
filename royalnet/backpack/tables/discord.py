from sqlalchemy import Column, \
                       Integer, \
                       String, \
                       BigInteger, \
                       ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declared_attr
# noinspection PyUnresolvedReferences
from .users import User


class Discord:
    __tablename__ = "discord"

    @declared_attr
    def user_id(self):
        return Column(Integer, ForeignKey("users.uid"))

    @declared_attr
    def user(self):
        return relationship("User", backref="discord")

    @declared_attr
    def discord_id(self):
        return Column(BigInteger, primary_key=True)

    @declared_attr
    def username(self):
        return Column(String)

    @declared_attr
    def discriminator(self):
        return Column(String)

    @declared_attr
    def avatar_url(self):
        return Column(String)

    def __repr__(self):
        return f"<Discord {str(self)}>"

    def __str__(self):
        return f"[c]discord:{self.full_username()}[/c]"

    def full_username(self):
        return f"{self.username}#{self.discriminator}"
