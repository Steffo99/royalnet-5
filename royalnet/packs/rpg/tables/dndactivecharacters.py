from sqlalchemy import *
from sqlalchemy.orm import *
from sqlalchemy.ext.declarative import *


class DndActiveCharacter:
    __tablename__ = "dndactivecharacters"

    @declared_attr
    def character_id(self):
        return Column(Integer, ForeignKey("dndcharacters.character_id"), primary_key=True)

    @declared_attr
    def user_id(self):
        return Column(Integer, ForeignKey("users.uid"), primary_key=True)

    @declared_attr
    def character(self):
        return relationship("DndCharacter", foreign_keys=self.character_id, backref="activations", use_scalar=True)

    @declared_attr
    def user(self):
        return relationship("User", foreign_keys=self.user_id, backref="active_dnd_character", use_scalar=True)

    def __repr__(self):
        return f"<{self.__class__.__qualname__} for {self.user_id}: {self.character_id}>"
