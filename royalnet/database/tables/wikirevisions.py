from sqlalchemy import Column, \
                       Integer, \
                       Text, \
                       DateTime, \
                       ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declared_attr
# noinspection PyUnresolvedReferences
from .wikipages import WikiPage
# noinspection PyUnresolvedReferences
from .royals import Royal


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
        return Column(UUID(as_uuid=True), ForeignKey("wikipages.page_id"), nullable=False)

    @declared_attr
    def page(self):
        return relationship("WikiPage", foreign_keys=self.page_id, backref="revisions")

    @declared_attr
    def author_id(self):
        return Column(Integer, ForeignKey("royals.uid"), nullable=False)

    @declared_attr
    def author(self):
        return relationship("Royal", foreign_keys=self.author_id, backref="wiki_contributions")

    @declared_attr
    def timestamp(self):
        return Column(DateTime, nullable=False)

    @declared_attr
    def reason(self):
        return Column(Text)

    @declared_attr
    def diff(self):
        return Column(Text)
