from sqlalchemy import Column, \
                       Integer, \
                       ForeignKey
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.declarative import declared_attr
from .royals import Royal


class TriviaScore:
    __tablename__ = "triviascores"

    @declared_attr
    def royal_id(self):
        return Column(Integer, ForeignKey("royals.uid"), primary_key=True)

    @declared_attr
    def royal(self):
        return relationship("Royal", backref=backref("trivia_score", uselist=False))

    @declared_attr
    def correct_answers(self):
        return Column(Integer, nullable=False, default=0)

    @declared_attr
    def wrong_answers(self):
        return Column(Integer, nullable=False, default=0)

    def __repr__(self):
        return f"<TriviaScore of {self.royal}: ({self.correct_answers}|{self.wrong_answers})>"
