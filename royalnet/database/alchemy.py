from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from .tables import Royal
from ..utils import classdictjanitor


class Alchemy:
    def __init__(self, database_uri: str = "sqlite://"):
        self.engine = create_engine(database_uri)
        self.Base = declarative_base(bind=self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self._create_tables()

    def _create_tables(self):
        self.Royal = type("Royal", (self.Base,), classdictjanitor(Royal))
        self.Base.metadata.create_all()
