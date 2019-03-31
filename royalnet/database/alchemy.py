import typing
import asyncio
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from contextlib import asynccontextmanager
from ..utils import classdictjanitor

loop = asyncio.get_event_loop()


class Alchemy:
    def __init__(self, database_uri: str = "sqlite://", tables: typing.Optional[typing.List] = None):
        self.engine = create_engine(database_uri)
        self.Base = declarative_base(bind=self.engine)
        self._Session = sessionmaker(bind=self.engine)
        self._create_tables(tables)

    def _create_tables(self, tables: typing.Optional[typing.List]):
        for table in tables:
            name = table.__name__
            try:
                self.__getattribute__(name)
            except AttributeError:
                # Actually the intended result
                self.__setattr__(name, type(name, (self.Base,), classdictjanitor(table)))
            else:
                raise NameError(f"{name} is a reserved name and can't be used as a table name")
        self.Base.metadata.create_all()

    @asynccontextmanager
    async def Session(self):
        session = await loop.run_in_executor(None, self._Session)
        try:
            yield session
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
