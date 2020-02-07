from sqlalchemy import Column, \
                       Integer, \
                       String, \
                       ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declared_attr
import royalnet.utils as ru


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
        return relationship("User", backref="aliases")

    @classmethod
    async def find_user(cls, alchemy, session, alias: str):
        result = await ru.asyncify(session.query(alchemy.get(cls)).filter_by(alias=alias.lower()).one_or_none)
        if result is not None:
            result = result.user
        return result

    def __init__(self, user: str, alias: str):
        self.user = user
        self.alias = alias.lower()

    def __repr__(self):
        return f"<Alias {str(self)}>"

    def __str__(self):
        return f"{self.alias}->{self.user_id}"
