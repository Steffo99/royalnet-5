from enum import Enum
from sqlalchemy import Column, \
                       Integer, \
                       String, \
                       LargeBinary


class Role(Enum):
    Guest = "Guest"
    Member = "Member"
    Admin = "Admin"


class Royal:
    __tablename__ = "royals"

    uid = Column(Integer, unique=True, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    password = Column(LargeBinary)
    role = Column(String, nullable=False)
