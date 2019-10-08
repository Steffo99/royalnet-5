from sqlalchemy import Column, \
                       Integer, \
                       String, \
                       ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declared_attr
from .users import User
from .mmevents import MMEvent


class MMResponse:
    __tablename__ = "mmresponse"

    @declared_attr
    def royal_id(self):
        return Column(Integer, ForeignKey("users.uid"), primary_key=True)

    @declared_attr
    def royal(self):
        return relationship("User", backref="mmresponses_given")

    @declared_attr
    def mmevent_id(self):
        return Column(Integer, ForeignKey("mmevents.mmid"), primary_key=True)

    @declared_attr
    def mmevent(self):
        return relationship("MMEvent", backref="responses")

    @declared_attr
    def response(self):
        # Valid decisions are YES, LATER or NO
        return Column(String)

    def __repr__(self):
        return f"<MMResponse of {self.royal}: {self.response}>"
