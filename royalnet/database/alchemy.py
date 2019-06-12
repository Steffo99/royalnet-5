import typing
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from contextlib import contextmanager, asynccontextmanager
from ..utils import asyncify
# noinspection PyUnresolvedReferences
from ..error import InvalidConfigError


class Alchemy:
    """A wrapper around SQLAlchemy declarative that allows to use multiple databases at once while maintaining a single table-class for both of them."""

    def __init__(self, database_uri: str, tables: typing.Set):
        """Create a new Alchemy object.

        Args:
            database_uri: The uri of the database, as described at https://docs.sqlalchemy.org/en/13/core/engines.html .
            tables: The set of tables to be created and used in the selected database. Check the tables submodule for more details.
        """
        if database_uri.startswith("sqlite"):
            raise NotImplementedError("Support for sqlite databases is currently missing")
        self.engine = create_engine(database_uri)
        self.Base = declarative_base(bind=self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self._create_tables(tables)

    def _create_tables(self, tables: typing.Set):
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
    def session_cm(self):
        """Use Alchemy as a context manager (to be used in with statements)."""
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
        """Use Alchemy as a asyncronous context manager (to be used in async with statements)."""
        session = await asyncify(self.Session)
        try:
            yield session
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
