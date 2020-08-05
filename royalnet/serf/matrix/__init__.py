"""A :class:`Serf` implementation for Matrix.

It requires (obviously) the ``matrix`` extra to be installed.

Install it with: ::

    pip install royalnet[matrix]

"""

from .escape import escape
from .matrixserf import MatrixSerf

__all__ = [
    "MatrixSerf",
    "escape",
]
