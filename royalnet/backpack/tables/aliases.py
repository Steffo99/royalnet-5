from sqlalchemy import Column, \
    Integer, \
    String, \
    ForeignKey
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import relationship


class Alias:
    __tablename__ = "aliases"

    @declared_attr
    def user_id(self):
        return Column(Integer, ForeignKey("users.uid"), primary_key=True)

    @declared_attr
    def alias(self):
        return Column(String, primary_key=True)

    @declared_attr
    def user(self):
        return relationship("User", backref="_aliases")

    def __init__(self, user, alias: str):
        self.user = user
        self.alias = alias.lower()

    def __repr__(self):
        return f"<Alias {str(self)}>"

    def __str__(self):
        return f"{self.alias}->{self.user_id}"
