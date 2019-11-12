from typing import Type
from sqlalchemy.schema import Table


class AlchemyConfig:
    """A helper class to configure :class:`Alchemy` in a :class:`Serf`."""
    def __init__(self,
                 master_table: Type[Table],
                 identity_table: Type[Table],
                 ):
        self.master_table: Type[Table] = master_table
        self.identity_table: Type[Table] = identity_table