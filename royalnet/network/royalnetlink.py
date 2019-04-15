import asyncio
import websockets
import uuid
import functools
import typing
import pickle
import logging as _logging
from .messages import Message, ErrorMessage
from .packages import Package

loop = asyncio.get_event_loop()
log = _logging.getLogger(__name__)


class NotConnectedError(Exception):
    pass


class NotIdentifiedError(Exception):
    pass


class NetworkError(Exception):
    def __init__(self, error_msg: ErrorMessage, *args):
        super().__init__(*args)
        self.error_msg: ErrorMessage = error_msg


class PendingRequest:
    def __init__(self):
        self.event: asyncio.Event = asyncio.Event()
        self.data: Message = None

    def __repr__(self):
        if self.event.is_set():
            return f"<PendingRequest: {self.data.__class__.__name__}>"
        return f"<PendingRequest>"

    def set(self, data):
        self.data = data
        self.event.set()


def requires_connection(func):
    @functools.wraps(func)
    async def new_func(self, *args, **kwargs):
        await self._connect_event.wait()
        return await func(self, *args, **kwargs)
    return new_func


def requires_identification(func):
    @functools.wraps(func)
    async def new_func(self, *args, **kwargs):
        await self.identify_event.wait()
        return await func(self, *args, **kwargs)
    return new_func


class RoyalnetLink:
    def __init__(self, master_uri: str, secret: str, link_type: str, request_handler):
        assert ":" not in link_type
        self.master_uri: str = master_uri
        self.link_type: str = link_type
        self.nid: str = str(uuid.uuid4())
        self.secret: str = secret
        self.websocket: typing.Optional[websockets.WebSocketClientProtocol] = None
        self.request_handler = request_handler
        self._pending_requests: typing.Dict[typing.Optional[Message]] = {}
        self._connect_event: asyncio.Event = asyncio.Event()
        self.identify_event: asyncio.Event = asyncio.Event()

    async def connect(self):
        log.info(f"Connecting to {self.master_uri}...")
        self.websocket = await websockets.connect(self.master_uri)
        self._connect_event.set()
        log.info(f"Connected!")

    @requires_connection
    async def receive(self) -> Package:
        try:
            raw_pickle = await self.websocket.recv()
        except websockets.ConnectionClosed:
            self.websocket = None
            self._connect_event.clear()
            self.identify_event.clear()
            log.info(f"Connection to {self.master_uri} was closed.")
            # What to do now? Let's just reraise.
            raise
        package: typing.Union[Package, Package] = pickle.loads(raw_pickle)
        assert package.destination == self.nid
        log.debug(f"Received package: {package}")
        return package

    @requires_connection
    async def identify(self) -> None:
        log.info(f"Identifying to {self.master_uri}...")
        await self.websocket.send(f"Identify {self.nid}:{self.link_type}:{self.secret}")
        response_package = await self.receive()
        response = response_package.data
        if isinstance(response, ErrorMessage):
            raise NetworkError(response, "Server returned error while identifying self")
        self.identify_event.set()
        log.info(f"Identified successfully!")

    @requires_identification
    async def send(self, package: Package):
        raw_pickle: bytes = pickle.dumps(package)
        await self.websocket.send(raw_pickle)
        log.debug(f"Sent package: {package}")

    @requires_identification
    async def request(self, message, destination):
        package = Package(message, destination, self.nid)
        request = PendingRequest()
        self._pending_requests[package.source_conv_id] = request
        await self.send(package)
        log.debug(f"Sent request: {message} -> {destination}")
        await request.event.wait()
        result: Message = request.data
        log.debug(f"Received response: {request} -> {result}")
        if isinstance(result, ErrorMessage):
            raise NetworkError(result, "Server returned error while requesting something")
        return result

    async def run(self):
        log.debug(f"Running main client loop for {self.nid}.")
        while True:
            if self.websocket is None:
                await self.connect()
            if not self.identify_event.is_set():
                await self.identify()
            package: Package = await self.receive()
            # Package is a response
            if package.destination_conv_id in self._pending_requests:
                request = self._pending_requests[package.destination_conv_id]
                request.set(package.data)
                continue
            # Package is a request
            assert isinstance(package, Package)
            log.debug(f"Received request {package.source_conv_id}: {package}")
            response = await self.request_handler(package.data)
            if response is not None:
                response_package: Package = package.reply(response)
                await self.send(response_package)
                log.debug(f"Replied to request {response_package.source_conv_id}: {response_package}")
