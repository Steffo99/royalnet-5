from sqlalchemy import Column, \
                       Integer, \
                       String, \
                       LargeBinary


class Royal:
    __tablename__ = "royals"

    uid = Column(Integer, unique=True, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    password = Column(LargeBinary)
    role = Column(String, nullable=False)
    avatar = Column(LargeBinary)

    def __repr__(self):
        return f"<Royal {self.username}>"

    def __str__(self):
        return f"[c]royalnet:{self.username}[/c]"
