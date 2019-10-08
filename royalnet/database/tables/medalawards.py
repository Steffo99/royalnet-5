from sqlalchemy import Column, \
                       Integer, \
                       DateTime, \
                       ForeignKey
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import relationship
from .users import User
from .medals import Medal


class MedalAward:
    __tablename__ = "MedalAward"

    @declared_attr
    def award_id(self):
        return Column(Integer, primary_key=True)

    @declared_attr
    def date(self):
        return Column(DateTime)

    @declared_attr
    def medal_id(self):
        return Column(Integer, ForeignKey("medals.mid"), nullable=False)

    @declared_attr
    def royal_id(self):
        return Column(Integer, ForeignKey("users.uid"), nullable=False)

    @declared_attr
    def medal(self):
        return relationship("Medal", backref="awarded_to")

    @declared_attr
    def royal(self):
        return relationship("User", backref="medals_received")

    def __repr__(self):
        return f"<MedalAward of {self.medal} to {self.royal} on {self.date}>"
