from sqlalchemy import Column, \
                       Integer, \
                       Text, \
                       Boolean, \
                       DateTime, \
                       ForeignKey, \
                       String
from sqlalchemy.orm import relationship
from .royals import Royal


class Diario:
    __tablename__ = "diario"

    diario_id = Column(Integer, primary_key=True)

    creator_id = Column(Integer, ForeignKey("royals.id"))
    quoted_id = Column(Integer, ForeignKey("royals.id"))
    quoted_name = Column(String)
    text = Column(Text, nullable=False)
    context = Column(Text)
    timestamp = Column(DateTime, nullable=False)
    media_url = Column(String)
    spoiler = Column(Boolean, default=False)

    creator = relationship("Royal", foreign_keys=creator_id, backref="diario_created")
    quoted = relationship("Royal", foreign_keys=quoted_id, backref="diario_quoted")

    def __repr__(self):
        return f"<Diario {self.diario_id}>"

    def __str__(self):
        return f"diario:{self.diario_id}"
