import uuid
import typing
from asyncio import Event


class RoyalnetData:
    """A class to hold data to be sent to the Royalnet."""
    def __init__(self, data):
        self.uuid = str(uuid.uuid4())
        self.request = data
        self.event = Event()
        self.response = None

    def send(self):
        """TODO EVERYTHING"""



class RoyalnetWait:
    """A class that represents a data request sent to the Royalnet."""
    def __init__(self):
        self.event = Event()
        self.data = None

    def receive(self, data):
        self.data = data
        self.event.set()

    async def get(self):
        await self.event.wait()
        return self.data


class RoyalnetDict:
    """A dictionary used to asyncrounosly hold data received from the Royalnet."""

    def __init__(self):
        self.dict: typing.Dict[str, RoyalnetRequest] = {}

    async def request(self, data: RoyalnetWait):
