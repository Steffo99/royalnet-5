from typing import *


class Response:
    """A base class to be inherited by all other response types."""

    def to_dict(self) -> dict:
        """Prepare the Response to be sent by converting it to a JSONable :py:class:`dict`."""
        return {
            "type": self.__class__.__name__,
            **self.__dict__
        }

    def __eq__(self, other):
        if isinstance(other, Response):
            return self.to_dict() == other.to_dict()
        return False

    @classmethod
    def from_dict(cls, d: dict) -> "Response":
        """Recreate the response from a received :py:class:`dict`."""
        # Ignore type in dict
        del d["type"]
        # noinspection PyArgumentList
        return cls(**d)


class ResponseSuccess(Response):
    """A response to a successful :py:class:`Request`."""

    def __init__(self, data: Optional[dict] = None):
        if data is None:
            self.data = {}
        else:
            self.data = data

    def __repr__(self):
        return f"{self.__class__.__qualname__}(data={self.data})"


class ResponseFailure(Response):
    """A response to a invalid :py:class:`Request`."""

    def __init__(self, name: str, description: str, extra_info: Optional[dict] = None):
        self.name: str = name
        self.description: str = description
        self.extra_info: Optional[dict] = extra_info

    def __repr__(self):
        return f"{self.__class__.__qualname__}(name={self.name}, description={self.description}, extra_info={self.extra_info})"
