import typing
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from ..utils import classdictjanitor


class Alchemy:
    def __init__(self, database_uri: str = "sqlite://", tables: typing.Optional[typing.List] = None):
        self.engine = create_engine(database_uri)
        self.Base = declarative_base(bind=self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self._create_tables(tables)

    def _create_tables(self, tables: typing.Optional[typing.List]):
        for table in tables:
            name = table.__name__
            self.__setattr__(name, type(name, (self.Base,), classdictjanitor(table)))
        self.Base.metadata.create_all()
