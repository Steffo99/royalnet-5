from sqlalchemy import Column, \
                       Integer, \
                       String, \
                       ForeignKey
from sqlalchemy.orm import relationship
from .royals import Royal


class Alias:
    __tablename__ = "aliases"

    royal_id = Column(Integer, ForeignKey("royals.uid"))
    alias = Column(String, primary_key=True)

    royal = relationship("Royal", backref="aliases")

    def __repr__(self):
        return f"<Alias {str(self)}>"

    def __str__(self):
        return f"{self.alias}->{self.royal_id}"
