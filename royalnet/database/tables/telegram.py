from sqlalchemy import Column, \
                       Integer, \
                       String, \
                       BigInteger, \
                       ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declared_attr
# noinspection PyUnresolvedReferences
from .royals import Royal


class Telegram:
    __tablename__ = "telegram"

    @declared_attr
    def royal_id(self):
        return Column(Integer, ForeignKey("royals.uid"))

    @declared_attr
    def tg_id(self):
        return Column(BigInteger, primary_key=True)

    @declared_attr
    def first_name(self):
        return Column(String)

    @declared_attr
    def last_name(self):
        return Column(String)

    @declared_attr
    def username(self):
        return Column(String)

    @declared_attr
    def royal(self):
        return relationship("Royal", backref="telegram")

    def __repr__(self):
        return f"<Telegram {str(self)}>"

    def __str__(self):
        return f"[c]telegram:{self.mention()}[/c]"

    def mention(self) -> str:
        if self.username is not None:
            return f"@{self.username}"
        elif self.last_name is not None:
            return f"{self.first_name} {self.last_name}"
        else:
            return self.first_name
