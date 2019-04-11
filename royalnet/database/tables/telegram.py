from sqlalchemy import Column, \
                       Integer, \
                       String, \
                       BigInteger, \
                       LargeBinary, \
                       ForeignKey
from sqlalchemy.orm import relationship
from .royals import Royal


class Telegram:
    __tablename__ = "telegram"

    royal_id = Column(Integer, ForeignKey("royals.uid"))
    tg_id = Column(BigInteger, primary_key=True)
    first_name = Column(String)
    last_name = Column(String)
    username = Column(String)

    royal = relationship("Royal", backref="telegram")

    def __repr__(self):
        return f"<Telegram {str(self)}>"

    def __str__(self):
        return f"[c]telegram:{self.mention()}[/c]"

    def mention(self) -> str:
        if self.username is not None:
            return f"@{self.username}"
        elif self.last_name is not None:
            return f"{self.first_name} {self.last_name}"
        else:
            return self.first_name
