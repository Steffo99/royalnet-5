from sqlalchemy import *
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declared_attr
# noinspection PyUnresolvedReferences
from .users import User
import re


class Matrix:
    __tablename__ = "matrix"

    @declared_attr
    def user_id(self):
        return Column(Integer, ForeignKey("users.uid"))

    @declared_attr
    def user(self):
        return relationship("User", backref="matrix")

    @declared_attr
    def matrix_id(self):
        return Column(String, nullable=False, primary_key=True)

    @property
    def username(self):
        match = re.match("^@(.+):.+$", self.matrix_id)
        result = match.group(1)
        assert result is not None
        return result

    @property
    def homeserver(self):
        match = re.match("^@.+:(.+)$", self.matrix_id)
        result = match.group(1)
        assert result is not None
        return result

    def __repr__(self):
        return f"<Matrix {str(self)}>"

    def __str__(self):
        return f"[c]matrix:{self.matrix_id}[/c]"
