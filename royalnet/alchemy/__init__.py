"""The subpackage providing all functions and classes related to databases and tables.

It requires either the ``alchemy_easy`` or the ``alchemy_hard`` extras to be installed.

You can install ``alchemy_easy`` with: ::

    pip install royalnet[alchemy_easy]

To install ``alchemy_hard``, refer to the `psycopg2 <https://pypi.org/project/psycopg2/>}`_ installation instructions,
then run: ::

    pip install royalnet[alchemy_hard]

"""

from .alchemy import Alchemy
from .table_dfs import table_dfs
from .errors import *

__all__ = [
    "Alchemy",
    "table_dfs",
    "AlchemyException",
    "TableNotFoundError",
]
