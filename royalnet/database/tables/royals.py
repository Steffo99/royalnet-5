from sqlalchemy import Column, \
                       Integer, \
                       String, \
                       LargeBinary
from sqlalchemy.ext.declarative import declared_attr


class Royal:
    __tablename__ = "royals"

    @declared_attr
    def uid(self):
        return Column(Integer, unique=True, primary_key=True)

    @declared_attr
    def username(self):
        return Column(String, unique=True, nullable=False)

    @declared_attr
    def password(self):
        return Column(LargeBinary)

    @declared_attr
    def role(self):
        return Column(String, nullable=False)

    @declared_attr
    def avatar(self):
        return Column(LargeBinary)

    def __repr__(self):
        return f"<Royal {self.username}>"

    def __str__(self):
        return f"[c]royalnet:{self.username}[/c]"
