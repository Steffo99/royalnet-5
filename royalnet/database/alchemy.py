import typing
import asyncio
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager, asynccontextmanager
from ..utils import cdj, asyncify

loop = asyncio.get_event_loop()


class Alchemy:
    def __init__(self, database_uri: str, tables: typing.Optional[typing.Set] = None):
        if database_uri.startswith("sqlite"):
            raise NotImplementedError("Support for sqlite databases is currently missing")
        self.engine = create_engine(database_uri)
        self.Base = declarative_base(bind=self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self._create_tables(tables)

    def _create_tables(self, tables: typing.Optional[typing.List]):
        for table in tables:
            name = table.__name__
            try:
                self.__getattribute__(name)
            except AttributeError:
                # Actually the intended result
                # TODO: here is the problem!
                self.__setattr__(name, type(name, (self.Base, table), {}))
            else:
                raise NameError(f"{name} is a reserved name and can't be used as a table name")
        self.Base.metadata.create_all()

    @contextmanager
    async def session_cm(self):
        session = self.Session()
        try:
            yield session
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    @asynccontextmanager
    async def session_acm(self):
        session = await asyncify(self.Session)
        try:
            yield session
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
