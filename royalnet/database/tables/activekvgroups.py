from sqlalchemy import Column, \
                       String, \
                       Integer, \
                       ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declared_attr
# noinspection PyUnresolvedReferences
from .royals import Royal
# noinspection PyUnresolvedReferences
from .keygroups import Keygroup


class ActiveKvGroup:
    __tablename__ = "activekvgroups"

    @declared_attr
    def royal_id(self):
        return Column(Integer, ForeignKey("royals.uid"), primary_key=True)

    @declared_attr
    def group_name(self):
        return Column(String, ForeignKey("keygroups.group_name"), nullable=False)

    @declared_attr
    def royal(self):
        return relationship("Royal", backref="active_kv_group")

    @declared_attr
    def group(self):
        return relationship("Keygroup", backref="users_with_this_active")

    def __repr__(self):
        return f"<ActiveKvGroup royal={self.royal} group={self.group_name}>"
