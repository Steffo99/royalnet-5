from sqlalchemy import Column, \
                       Integer, \
                       String, \
                       ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declared_attr


class Alias:
    __tablename__ = "aliases"

    @declared_attr
    def royal_id(self):
        return Column(Integer, ForeignKey("users.uid"))

    @declared_attr
    def alias(self):
        return Column(String, primary_key=True)

    @declared_attr
    def royal(self):
        return relationship("User", backref="aliases")

    @classmethod
    def find_by_alias(cls, alchemy, session, alias: str):
        result = session.query(alchemy.get(cls)).filter_by(alias=alias.lower()).one_or_none()
        if result is not None:
            result = result.royal
        return result

    def __repr__(self):
        return f"<Alias {str(self)}>"

    def __str__(self):
        return f"{self.alias}->{self.royal_id}"
