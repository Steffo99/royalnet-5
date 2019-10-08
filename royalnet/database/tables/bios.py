from sqlalchemy import Column, \
                       Integer, \
                       Text, \
                       ForeignKey
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.declarative import declared_attr
from .users import User


class Bio:
    __tablename__ = "bios"

    @declared_attr
    def royal_id(self):
        return Column(Integer, ForeignKey("users.uid"), primary_key=True)

    @declared_attr
    def royal(self):
        return relationship("User", backref=backref("bio", uselist=False))

    @declared_attr
    def contents(self):
        return Column(Text, nullable=False, default="")

    def __repr__(self):
        return f"<Bio of {self.royal}>"

    def __str__(self):
        return self.contents
