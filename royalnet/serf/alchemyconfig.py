from typing import Type
from sqlalchemy.schema import Table


class AlchemyConfig:
    """A helper class to configure :class:`Alchemy` in a :class:`Serf`."""
    def __init__(self,
                 database_url: str,
                 master_table: Type[Table],
                 identity_table: Type[Table],
                 identity_column: str):
        self.database_url: str = database_url
        self.master_table: Type[Table] = master_table
        self.identity_table: Type[Table] = identity_table
        self.identity_column: str = identity_column

    def __repr__(self):
        return f"<{self.__class__.__qualname__} for {self.server_url}>"