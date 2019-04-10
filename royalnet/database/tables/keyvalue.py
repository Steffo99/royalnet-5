from sqlalchemy import Column, \
                       String, \
                       ForeignKey
from sqlalchemy.orm import relationship
from .keygroup import Keygroup


class Keyvalue:
    __tablename__ = "keyvalues"

    group_name = Column(String, ForeignKey("keygroups.group_name"), primary_key=True)
    key = Column(String, primary_key=True)
    value = Column(String, nullable=False)

    group = relationship("Keygroup")

    def __repr__(self):
        return f"<Keyvalue group={self.group_name} key={self.key} value={self.value}>"

    def __str__(self):
        return f"{self.key}: [b]{self.value}[/b]"
