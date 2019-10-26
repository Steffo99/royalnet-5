from sqlalchemy import *
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declared_attr
from ..utils import MMChoice


class MMResponse:
    __tablename__ = "mmresponse"

    @declared_attr
    def user_id(self):
        return Column(Integer, ForeignKey("users.uid"), primary_key=True)

    @declared_attr
    def user(self):
        return relationship("User", backref="mmresponses_given")

    @declared_attr
    def mmevent_id(self):
        return Column(Integer, ForeignKey("mmevents.mmid"), primary_key=True)

    @declared_attr
    def mmevent(self):
        return relationship("MMEvent", backref="responses")

    @declared_attr
    def choice(self):
        return Column(Enum(MMChoice), nullable=False)

    def __repr__(self):
        return f"<MMResponse of {self.user}: {self.choice}>"
