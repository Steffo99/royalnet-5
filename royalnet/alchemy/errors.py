class AlchemyException(Exception):
    """Base class for Alchemy exceptions."""


class TableNotFoundError(AlchemyException):
    """The requested table was not found."""
