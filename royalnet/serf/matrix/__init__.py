"""A :class:`Serf` implementation for Matrix.

It requires (obviously) the ``matrix`` extra to be installed.

Install it with: ::

    pip install royalnet[matrix]

"""

from .matrixserf import MatrixSerf
from .escape import escape

__all__ = [
    "MatrixSerf",
    "escape",
]
