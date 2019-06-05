from sqlalchemy import Column, \
                       Integer, \
                       Text, \
                       DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declared_attr
# noinspection PyUnresolvedReferences
from .royals import Royal


class WikiPage:
    """Wiki page properties."""
    __tablename__ = "wikipages"


class WikiRevision:
    """A wiki page revision.

    Warning:
        Requires PostgreSQL!"""
    __tablename__ = "wikirevisions"

    @declared_attr
    def revision_id(self):
        return Column(UUID(as_uuid=True), primary_key=True)

    @declared_attr
    def page_id(self):
        return Column(UUID(as_uuid=True), nullable=False)

    @declared_attr
    def content(self):
        return Column(Text, nullable=False)

    @declared_attr
    def timestamp(self):
        return Column(DateTime, nullable=False)

    @declared_attr
    def reason(self):
        return Column(Text)

    @declared_attr
    def