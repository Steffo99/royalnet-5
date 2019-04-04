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
    creator_id = Column(Integer, ForeignKey("royals.uid"))
    quoted_account_id = Column(Integer, ForeignKey("royals.uid"))
    quoted = Column(String)
    text = Column(Text, nullable=False)
    context = Column(Text)
    timestamp = Column(DateTime, nullable=False)
    media_url = Column(String)
    spoiler = Column(Boolean, default=False)

    creator = relationship("Royal", foreign_keys=creator_id, backref="diario_created")
    quoted_account = relationship("Royal", foreign_keys=quoted_account_id, backref="diario_quoted")

    def __repr__(self):
        return f"<Diario diario_id={self.diario_id} creator_id={self.creator_id} quoted_account_id={self.quoted_account_id} quoted={self.quoted} text={self.text} context={self.context} timestamp={self.timestamp} media_url={self.media_url} spoiler={self.spoiler}>"
