from sqlalchemy import Column, \
                       String, \
                       ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declared_attr
# noinspection PyUnresolvedReferences
from .keygroups import Keygroup


class Keyvalue:
    __tablename__ = "keyvalues"

    @declared_attr
    def group_name(self):
        return Column(String, ForeignKey("keygroups.group_name"), primary_key=True)

    @declared_attr
    def key(self):
        return Column(String, primary_key=True)

    @declared_attr
    def value(self):
        return Column(String, nullable=False)

    @declared_attr
    def group(self):
        return relationship("Keygroup")

    def __repr__(self):
        return f"<Keyvalue group={self.group_name} key={self.key} value={self.value}>"

    def __str__(self):
        return f"{self.key}: [b]{self.value}[/b]"
