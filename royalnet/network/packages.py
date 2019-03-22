import pickle
import uuid


class Package:
    def __init__(self, data, destination: str, source: str, *, conversation_id: str = None):
        self.data = data
        self.destination: str = destination
        self.source = source
        self.conversation_id = conversation_id or str(uuid.uuid4())

    def __repr__(self):
        return f"<Package to {self.destination}: {self.data.__class__.__name__}>"

    def reply(self, data) -> "Package":
        return Package(data, self.source, self.destination, conversation_id=self.conversation_id)

    def pickle(self):
        return pickle.dumps(self)
