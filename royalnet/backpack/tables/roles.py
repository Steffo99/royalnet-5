from sqlalchemy import Column, \
                       Integer, \
                       String, \
                       ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declared_attr


class Role:
    __tablename__ = "role"

    @declared_attr
    def user_id(self):
        return Column(Integer, ForeignKey("users.uid"), primary_key=True)

    @declared_attr
    def role(self):
        return Column(String, primary_key=True)

    @declared_attr
    def user(self):
        return relationship("User", backref="_roles")

    def __init__(self, user, role: str):
        self.user = user
        self.role = role.lower()

    def __repr__(self):
        return f"<Alias {str(self)}>"

    def __str__(self):
        return f"{self.role}->{self.user_id}"
