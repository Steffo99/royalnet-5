from sqlalchemy import *
from sqlalchemy.orm import *
from sqlalchemy.ext.declarative import *


class DndCharacter:
    __tablename__ = "dndcharacters"

    @declared_attr
    def character_id(self):
        return Column(Integer, primary_key=True)

    @declared_attr
    def creator_id(self):
        return Column(Integer, ForeignKey("users.uid"))

    @declared_attr
    def creator(self):
        return relationship("User", foreign_keys=self.creator_id, backref="dndcharacters_created")

    @declared_attr
    def name(self):
        return Column(String)

    @declared_attr
    def strength(self):
        return Column(Integer)

    @property
    def strength_mod(self):
        return (self.strength - 10) // 2

    @declared_attr
    def dexterity(self):
        return Column(Integer)

    @property
    def dexterity_mod(self):
        return (self.dexterity - 10) // 2

    @declared_attr
    def constitution(self):
        return Column(Integer)

    @property
    def constitution_mod(self):
        return (self.constitution - 10) // 2

    @declared_attr
    def intelligence(self):
        return Column(Integer)

    @property
    def intelligence_mod(self):
        return (self.intelligence - 10) // 2

    @declared_attr
    def wisdom(self):
        return Column(Integer)

    @property
    def wisdom_mod(self):
        return (self.wisdom - 10) // 2

    @declared_attr
    def charisma(self):
        return Column(Integer)

    @property
    def charisma_mod(self):
        return (self.charisma - 10) // 2

    @declared_attr
    def level(self):
        return Column(Integer)

    @property
    def proficiency_bonus(self):
        return ((self.level - 1) // 4) + 2

    @declared_attr
    def max_hp(self):
        return Column(Integer)

    @declared_attr
    def armor_class(self):
        return Column(Integer)

    def __repr__(self):
        return f"<{self.__class__.__qualname__} {self.name}>"

    def __str__(self):
        return f"{self.name}"

    def character_sheet(self):
        return f"{self.name}\n" \
               f"LV {self.level}\n\n" \
               f"STR {self.strength}\n" \
               f"DEX {self.dexterity}\n" \
               f"CON {self.constitution}\n" \
               f"INT {self.intelligence}\n" \
               f"WIS {self.wisdom}\n" \
               f"CHA {self.charisma}\n\n" \
               f"MAXHP {self.max_hp}\n" \
               f"AC {self.armor_class}\n" \
