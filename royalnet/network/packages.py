import pickle
import uuid


class Package:
    """A Royalnet package, the data type with which a :py:class:`royalnet.network.RoyalnetLink` communicates with a :py:class:`royalnet.network.RoyalnetServer` or another link. """

    def __init__(self, data, destination: str, source: str, *, source_conv_id: str = None, destination_conv_id: str = None):
        """Create a Package.

        Parameters:
            data: The data that should be sent. Usually a :py:class:`royalnet.network.Message`.
            destination: The ``link_type`` of the destination node, or alternatively, the ``nid`` of the node. Can also be the ``NULL`` value to send the message to nobody.
            source: The ``nid`` of the node that created this Package.
            source_conv_id: The conversation id of the node that created this package. Akin to the sequence number on IP packets.
            destination_conv_id: The conversation id of the node that this Package is a reply to."""
        # TODO: something is not right in these type hints. Check them.
        self.data = data
        self.destination: str = destination
        self.source: str = source
        self.source_conv_id: str = source_conv_id or str(uuid.uuid4())
        self.destination_conv_id: str = destination_conv_id

    def __repr__(self):
        return f"<Package to {self.destination}: {self.data.__class__.__name__}>"

    def reply(self, data) -> "Package":
        """Reply to this Package with another Package.

        Parameters:
            data: The data that should be sent. Usually a :py:class:`royalnet.network.Message`.

        Returns:
            The reply Package."""
        return Package(data, self.source, self.destination,
                       source_conv_id=str(uuid.uuid4()),
                       destination_conv_id=self.source_conv_id)

    def pickle(self) -> bytes:
        """:py:mod:`pickle` this Package.

        Returns:
            The pickled package in form of bytes."""
        return pickle.dumps(self)
