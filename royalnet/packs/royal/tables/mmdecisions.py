from sqlalchemy import Column, \
                       Integer, \
                       String, \
                       ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declared_attr


class MMDecision:
    __tablename__ = "mmdecisions"

    @declared_attr
    def royal_id(self):
        return Column(Integer, ForeignKey("users.uid"), primary_key=True)

    @declared_attr
    def royal(self):
        return relationship("User", backref="mmdecisions_taken")

    @declared_attr
    def mmevent_id(self):
        return Column(Integer, ForeignKey("mmevents.mmid"), primary_key=True)

    @declared_attr
    def mmevent(self):
        return relationship("MMEvent", backref="decisions")

    @declared_attr
    def decision(self):
        # Valid decisions are YES, MAYBE or NO
        return Column(String, nullable=False)

    def __repr__(self):
        return f"<MMDecision of {self.royal}: {self.decision}>"
