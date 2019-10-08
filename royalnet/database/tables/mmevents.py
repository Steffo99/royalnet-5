import telegram
import typing
from sqlalchemy import Column, \
                       Integer, \
                       DateTime, \
                       String, \
                       Text, \
                       ForeignKey, \
                       BigInteger
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declared_attr
from .users import User
if typing.TYPE_CHECKING:
    from .mmdecisions import MMDecision
    from .mmresponse import MMResponse


class MMEvent:
    __tablename__ = "mmevents"

    @declared_attr
    def creator_id(self):
        return Column(Integer, ForeignKey("users.uid"), nullable=False)

    @declared_attr
    def creator(self):
        return relationship("User", backref="mmevents_created")

    @declared_attr
    def mmid(self):
        return Column(Integer, primary_key=True)

    @declared_attr
    def datetime(self):
        return Column(DateTime, nullable=False)

    @declared_attr
    def title(self):
        return Column(String, nullable=False)

    @declared_attr
    def description(self):
        return Column(Text, nullable=False, default="")

    @declared_attr
    def state(self):
        # Valid states are WAITING, DECISION, READY_CHECK, STARTED
        return Column(String, nullable=False, default="WAITING")

    @declared_attr
    def message_id(self):
        return Column(BigInteger)

    def __repr__(self):
        return f"<MMEvent {self.mmid}: {self.title}>"

