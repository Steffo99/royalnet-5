from sqlalchemy import Column, \
                       Integer, \
                       String, \
                       ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declared_attr
# noinspection PyUnresolvedReferences
from .royals import Royal


class Alias:
    __tablename__ = "aliases"

    @declared_attr
    def royal_id(self):
        return Column(Integer, ForeignKey("royals.uid"))

    @declared_attr
    def alias(self):
        return Column(String, primary_key=True)

    @declared_attr
    def royal(self):
        return relationship("Royal", backref="aliases")

    def __repr__(self):
        return f"<Alias {str(self)}>"

    def __str__(self):
        return f"{self.alias}->{self.royal_id}"
