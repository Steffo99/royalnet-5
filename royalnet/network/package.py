import json
import uuid
import typing


class Package:
    """A Royalnet package, the data type with which a :py:class:`royalnet.network.RoyalnetLink` communicates with a :py:class:`royalnet.network.RoyalnetServer` or another link.
    Contains info about the source and the destination."""

    def __init__(self,
                 data: dict,
                 *,
                 source: str,
                 destination: str,
                 source_conv_id: typing.Optional[str] = None,
                 destination_conv_id: typing.Optional[str] = None):
        """Create a Package.

        Parameters:
            data: The data that should be sent. Usually a :py:class:`royalnet.network.Message`.
            source: The ``nid`` of the node that created this Package.
            destination: The ``link_type`` of the destination node, or alternatively, the ``nid`` of the node. Can also be the ``NULL`` value to send the message to nobody.
            source_conv_id: The conversation id of the node that created this package. Akin to the sequence number on IP packets.
            destination_conv_id: The conversation id of the node that this Package is a reply to."""
        # TODO: something is not right in these type hints. Check them.
        self.data: dict = data
        self.source: str = source
        self.source_conv_id: str = source_conv_id or str(uuid.uuid4())
        self.destination: str = destination
        self.destination_conv_id: typing.Optional[str] = destination_conv_id

    def __repr__(self):
        return f"<Package {self.source} ({self.source_conv_id}) to {self.destination} ({self.destination_conv_id}>"

    def __eq__(self, other):
        if isinstance(other, Package):
            return (self.data == other.data) and \
                   (self.source == other.source) and \
                   (self.destination == other.destination) and \
                   (self.source_conv_id == other.source_conv_id) and \
                   (self.destination_conv_id == other.destination_conv_id)
        return False

    def reply(self, data) -> "Package":
        """Reply to this Package with another Package.

        Parameters:
            data: The data that should be sent. Usually a :py:class:`royalnet.network.Message`.

        Returns:
            The reply Package."""
        return Package(data,
                       source=self.destination,
                       destination=self.source,
                       source_conv_id=self.destination_conv_id or str(uuid.uuid4()),
                       destination_conv_id=self.source_conv_id)

    @staticmethod
    def from_dict(d) -> "Package":
        """Create a Package from a dictionary."""
        if "source" not in d:
            raise ValueError("Missing source field")
        if "nid" not in d["source"]:
            raise ValueError("Missing source.nid field")
        if "conv_id" not in d["source"]:
            raise ValueError("Missing source.conv_id field")
        if "destination" not in d:
            raise ValueError("Missing destination field")
        if "nid" not in d["destination"]:
            raise ValueError("Missing destination.nid field")
        if "conv_id" not in d["destination"]:
            raise ValueError("Missing destination.conv_id field")
        if "data" not in d:
            raise ValueError("Missing data field")
        return Package(d["data"],
                       source=d["source"]["nid"],
                       destination=d["destination"]["nid"],
                       source_conv_id=d["source"]["conv_id"],
                       destination_conv_id=d["destination"]["conv_id"])

    def to_dict(self) -> dict:
        """Convert the Package into a dictionary."""
        return {
            "source": {
                "nid": self.source,
                "conv_id": self.source_conv_id
            },
            "destination": {
                "nid": self.destination,
                "conv_id": self.destination_conv_id
            },
            "data": self.data
        }

    @staticmethod
    def from_json_string(string: str) -> "Package":
        """Create a Package from a JSON string."""
        return Package.from_dict(json.loads(string))

    def to_json_string(self) -> str:
        """Convert the Package into a JSON string."""
        return json.dumps(self.to_dict())

    @staticmethod
    def from_json_bytes(b: bytes) -> "Package":
        """Create a Package from UTF8-encoded JSON bytes."""
        return Package.from_json_string(str(b, encoding="utf8"))

    def to_json_bytes(self) -> bytes:
        """Convert the Package into UTF8-encoded JSON bytes."""
        return bytes(self.to_json_string(), encoding="utf8")
