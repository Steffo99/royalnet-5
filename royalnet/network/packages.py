import pickle
import uuid


class Package:
    def __init__(self, data, destination: str, source: str, *, source_conv_id: str = None, destination_conv_id: str = None):
        self.data = data
        self.destination: str = destination
        self.source = source
        self.source_conv_id = source_conv_id or str(uuid.uuid4())
        self.destination_conv_id = destination_conv_id

    def __repr__(self):
        return f"<Package to {self.destination}: {self.data.__class__.__name__}>"

    def reply(self, data) -> "Package":
        return Package(data, self.source, self.destination,
                       source_conv_id=str(uuid.uuid4()),
                       destination_conv_id=self.source_conv_id)

    def pickle(self):
        return pickle.dumps(self)
