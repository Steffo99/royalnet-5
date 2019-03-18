import asyncio
from asyncio import Event
import websockets
import uuid
import functools
import typing
import pickle
from .messages import Message, ErrorMessage
from .packages import Package
loop = asyncio.get_event_loop()


class NotConnectedError(Exception):
    pass


class NotIdentifiedError(Exception):
    pass


class NetworkError(Exception):
    def __init__(self, error_msg: ErrorMessage, *args):
        super().__init__(*args)
        self.error_msg = error_msg


class PendingRequest:
    def __init__(self):
        self.event = Event()
        self.data = None

    def set(self, data):
        self.data = data
        self.event.set()


class RoyalnetLink:
    def __init__(self, master_uri: str, secret: str, link_type: str, request_handler):
        assert ":" not in link_type
        self.master_uri: str = master_uri
        self.link_type: str = link_type
        self.nid: str = str(uuid.uuid4())
        self.secret: str = secret
        self.websocket: typing.Optional[websockets.WebSocketClientProtocol] = None
        self.identified: bool = False
        self.request_handler = request_handler
        self._pending_requests: typing.Dict[typing.Optional[Message]] = {}

    async def connect(self):
        self.websocket = await websockets.connect(self.master_uri)

    def requires_connection(func):
        @functools.wraps(func)
        def new_func(self, *args, **kwargs):
            if self.websocket is None:
                raise NotConnectedError("Tried to call a method which @requires_connection while not connected")
            return func(self, *args, **kwargs)
        return new_func

    @requires_connection
    async def receive(self) -> Package:
        try:
            raw_pickle = await self.websocket.recv()
        except websockets.ConnectionClosed:
            self.websocket = None
            self.identified = False
            # What to do now? Let's just reraise.
            raise
        package: typing.Union[Package, Package] = pickle.loads(raw_pickle)
        assert package.destination == self.nid
        return package

    @requires_connection
    async def identify(self, secret) -> None:
        await self.websocket.send(f"Identify {self.nid}:{self.link_type}:{secret}")
        response_package = await self.receive()
        response = response_package.data
        if isinstance(response, ErrorMessage):
            raise NetworkError(response, "Server returned error while identifying self")
        self.identified = True

    def requires_identification(func):
        @functools.wraps(func)
        def new_func(self, *args, **kwargs):
            if not self.identified:
                raise NotIdentifiedError("Tried to call a method which @requires_identification while not identified")
            return func(self, *args, **kwargs)
        return new_func

    @requires_identification
    async def send(self, package: Package):
        raw_pickle: bytes = pickle.dumps(package)
        await self.websocket.send(raw_pickle)

    @requires_identification
    async def request(self, message, destination):
        package = Package(message, destination, self.nid)
        request = PendingRequest()
        self._pending_requests[package.conversation_id] = request
        await self.send(package)
        await request.event.wait()
        result = request.data
        if isinstance(result, ErrorMessage):
            raise NetworkError(result, "Server returned error while requesting something")
        return result

    async def run(self):
        while True:
            if self.websocket is None:
                await self.connect()
            if not self.identified:
                await self.identify()
            package: Package = self.receive()
            # Package is a response
            if package.conversation_id in self._pending_requests:
                request = self._pending_requests[package.conversation_id]
                request.set(package.data)
                continue
            # Package is a request
            assert isinstance(package, Package)
            response = await self.request_handler(package.data)
            if response is not None:
                response_package: Package = package.reply(response)
                await self.send(response_package)
