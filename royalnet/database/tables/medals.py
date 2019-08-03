from sqlalchemy import Column, \
                       Integer, \
                       String
from sqlalchemy.ext.declarative import declared_attr
# noinspection PyUnresolvedReferences
from .keygroups import Keygroup


class Medal:
    __tablename__ = "medals"

    @declared_attr
    def mid(self):
        return Column(Integer, primary_key=True)

    @declared_attr
    def name(self):
        return Column(String, nullable=False)

    @declared_attr
    def description(self):
        return Column(String)

    @declared_attr
    def icon(self):
        return Column(String)

    @declared_attr
    def classes(self):
        return Column(String, nullable=False, default="")

    @declared_attr
    def score(self):
        return Column(Integer, nullable=False)

    def __str__(self):
        return self.name

    def __repr__(self):
        return f"<Medal {self.mid}: {self.name}>"
