class AlchemyException(Exception):
    """Base class for Alchemy exceptions."""


class TableNotFoundException(AlchemyException):
    """The requested table was not found."""
