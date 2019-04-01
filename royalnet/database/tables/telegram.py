from sqlalchemy import Column, \
                       Integer, \
                       String, \
                       BigInteger, \
                       LargeBinary


class Telegram:
    __tablename__ = "telegram"

    royal_id = Column(Integer)
    tg_id = Column(BigInteger, primary_key=True)
    tg_first_name = Column(String)
    tg_last_name = Column(String)
    tg_username = Column(String)
    tg_avatar = Column(LargeBinary)

    def __repr__(self):
        return f"<Telegram {str(self)}>"

    def __str__(self):
        if self.tg_username is not None:
            return f"@{self.tg_username}"
        elif self.tg_last_name is not None:
            return f"{self.tg_first_name} {self.tg_last_name}"
        else:
            return self.tg_first_name

