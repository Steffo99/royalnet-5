from sqlalchemy import Column, \
                       Integer, \
                       String, \
                       BigInteger, \
                       ForeignKey
from sqlalchemy.orm import relationship
from .royals import Royal


class Discord:
    __tablename__ = "discord"

    royal_id = Column(Integer, ForeignKey("royals.uid"))
    discord_id = Column(BigInteger, primary_key=True)
    username = Column(String)
    discriminator = Column(String)
    avatar_hash = Column(String)

    royal = relationship("Royal", backref="discord")

    def __repr__(self):
        return f"<Discord {str(self)}>"

    def __str__(self):
        return f"[c]discord:{self.full_username()}[/c]"

    def full_username(self):
        return f"{self.username}#{self.discriminator}"
