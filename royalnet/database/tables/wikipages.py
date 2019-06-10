from sqlalchemy import Column, \
                       Text, \
                       String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declared_attr


class WikiPage:
    """Wiki page properties.

    Warning:
        Requires PostgreSQL!"""
    __tablename__ = "wikipages"

    @declared_attr
    def page_id(self):
        return Column(UUID(as_uuid=True), primary_key=True)

    @declared_attr
    def title(self):
        return Column(String, nullable=False)

    @declared_attr
    def content(self):
        return Column(Text)

    @declared_attr
    def format(self):
        return Column(String, nullable=False, default="markdown")

    @declared_attr
    def css(self):
        return Column(String)
