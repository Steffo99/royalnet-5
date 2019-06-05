from sqlalchemy import Column, \
                       Integer, \
                       Text, \
                       String
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declared_attr
# noinspection PyUnresolvedReferences
from .royals import Royal


class Wiki:
    __tablename__ = "wiki"

    @declared_attr
    def revision_id(self):
        return Column(String, primary_key=True)

    @declared_attr
    def page_id(self):
        return Column(Integer, nullable=False)

    @declared_attr
    def