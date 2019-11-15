from typing import TYPE_CHECKING


class AlchemyConfig:
    """A helper class to configure :class:`Alchemy` in a :class:`Serf`."""
    def __init__(self,
                 database_url: str,
                 master_table: type,
                 identity_table: type,
                 identity_column: str):
        self.database_url: str = database_url
        self.master_table: type = master_table
        self.identity_table: type = identity_table
        self.identity_column: str = identity_column

    def __repr__(self):
        return f"<{self.__class__.__qualname__} for {self.database_url}>"
