import re
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
    creator_id = Column(Integer, ForeignKey("royals.uid"), nullable=False)
    quoted_account_id = Column(Integer, ForeignKey("royals.uid"))
    quoted = Column(String)
    text = Column(Text)
    context = Column(Text)
    timestamp = Column(DateTime, nullable=False)
    media_url = Column(String)
    spoiler = Column(Boolean, default=False)

    creator = relationship("Royal", foreign_keys=creator_id, backref="diario_created")
    quoted_account = relationship("Royal", foreign_keys=quoted_account_id, backref="diario_quoted")

    def __repr__(self):
        return f"<Diario diario_id={self.diario_id} creator_id={self.creator_id} quoted_account_id={self.quoted_account_id} quoted={self.quoted} text={self.text} context={self.context} timestamp={self.timestamp} media_url={self.media_url} spoiler={self.spoiler}>"

    def __str__(self):
        # TODO: support media_url
        text = f"Riga #{self.diario_id}"
        text += f" (salvata da {str(self.creator)}"
        text += f" il {self.timestamp.strftime('%Y-%m-%d %H:%M')}):\n"
        if self.media_url is not None:
            text += f"{self.media_url}\n"
        if self.text is not None:
            if self.spoiler:
                hidden = re.sub(r"\w", "█", self.text)
                text += f"\"{hidden}\"\n"
            else:
                text += f"[b]\"{self.text}\"[/b]\n"
        if self.quoted_account is not None:
            text += f" —{str(self.quoted_account)}"
        elif self.quoted is not None:
            text += f" —{self.quoted}"
        else:
            text += f" —Anonimo"
        if self.context:
            text += f", [i]{self.context}[/i]"
        return text
