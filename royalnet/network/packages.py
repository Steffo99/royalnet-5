import pickle
import uuid


class Package:
    def __init__(self, data, destination: str, *, conversation_id: str = None):
        self.data = data
        self.destination: str = destination
        self.conversation_id = conversation_id or str(uuid.uuid4())

    def pickle(self):
        return pickle.dumps(self)


class TwoWayPackage(Package):
    def __init__(self, data, destination: str, source: str, *, conversation_id: str = None):
        super().__init__(data, destination, conversation_id=conversation_id)
        self.source = source

    def reply(self, data) -> Package:
        return Package(data, self.source, conversation_id=self.conversation_id)

    def two_way_reply(self, data) -> "TwoWayPackage":
        return TwoWayPackage(data, self.source, self.destination, conversation_id=self.conversation_id)
