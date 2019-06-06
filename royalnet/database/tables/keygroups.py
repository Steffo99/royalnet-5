from sqlalchemy import Column, \
                       String, \
                       ForeignKey
from sqlalchemy.ext.declarative import declared_attr


class Keygroup:
    __tablename__ = "keygroups"

    @declared_attr
    def group_name(self):
        return Column(String, ForeignKey("keygroups.group_name"), primary_key=True)

    def __repr__(self):
        return f"<Keygroup {self.group_name}>"
