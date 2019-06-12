import asyncio
import websockets
import uuid
import functools
import math
import numbers
import logging as _logging
import typing
from .package import Package


log = _logging.getLogger(__name__)


class NotConnectedError(Exception):
    """The :py:class:`royalnet.network.RoyalnetLink` is not connected to a :py:class:`royalnet.network.RoyalnetServer`."""


class NotIdentifiedError(Exception):
    """The :py:class:`royalnet.network.RoyalnetLink` has not identified yet to a :py:class:`royalnet.network.RoyalnetServer`."""


class ConnectionClosedError(Exception):
    """The :py:class:`royalnet.network.RoyalnetLink`'s connection was closed unexpectedly. The link can't be used anymore."""


class InvalidServerResponseError(Exception):
    """The :py:class:`royalnet.network.RoyalnetServer` sent invalid data to the :py:class:`royalnet.network.RoyalnetLink`."""


class NetworkError(Exception):
    def __init__(self, error_data: dict, *args):
        super().__init__(*args)
        self.error_data: dict = error_data


class PendingRequest:
    def __init__(self, *, loop: asyncio.AbstractEventLoop = None):
        if loop is None:
            self.loop = asyncio.get_event_loop()
        else:
            self.loop = loop
        self.event: asyncio.Event = asyncio.Event(loop=loop)
        self.data: typing.Optional[dict] = None

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
        await self.connect_event.wait()
        return await func(self, *args, **kwargs)
    return new_func


def requires_identification(func):
    @functools.wraps(func)
    async def new_func(self, *args, **kwargs):
        await self.identify_event.wait()
        return await func(self, *args, **kwargs)
    return new_func


class RoyalnetLink:
    def __init__(self, master_uri: str, secret: str, link_type: str, request_handler, *,
                 loop: asyncio.AbstractEventLoop = None):
        if ":" in link_type:
            raise ValueError("Link types cannot contain colons.")
        self.master_uri: str = master_uri
        self.link_type: str = link_type
        self.nid: str = str(uuid.uuid4())
        self.secret: str = secret
        self.websocket: typing.Optional[websockets.WebSocketClientProtocol] = None
        self.request_handler = request_handler
        self._pending_requests: typing.Dict[str, PendingRequest] = {}
        if loop is None:
            self._loop = asyncio.get_event_loop()
        else:
            self._loop = loop
        self.error_event: asyncio.Event = asyncio.Event(loop=self._loop)
        self.connect_event: asyncio.Event = asyncio.Event(loop=self._loop)
        self.identify_event: asyncio.Event = asyncio.Event(loop=self._loop)

    async def connect(self):
        """Connect to the :py:class:`royalnet.network.RoyalnetServer` at ``self.master_uri``."""
        log.info(f"Connecting to {self.master_uri}...")
        self.websocket = await websockets.connect(self.master_uri, loop=self._loop)
        self.connect_event.set()
        log.info(f"Connected!")

    @requires_connection
    async def receive(self) -> Package:
        """Recieve a :py:class:`Package` from the :py:class:`royalnet.network.RoyalnetServer`.

        Raises:
            :py:exc:`royalnet.network.royalnetlink.ConnectionClosedError` if the connection closes."""
        try:
            jbytes: bytes = await self.websocket.recv()
            package: Package = Package.from_json_bytes(jbytes)
        except websockets.ConnectionClosed:
            self.error_event.set()
            self.connect_event.clear()
            self.identify_event.clear()
            log.info(f"Connection to {self.master_uri} was closed.")
            # What to do now? Let's just reraise.
            raise ConnectionClosedError()
        if self.identify_event.is_set() and package.destination != self.nid:
            raise InvalidServerResponseError("Package is not addressed to this RoyalnetLink.")
        log.debug(f"Received package: {package}")
        return package

    @requires_connection
    async def identify(self) -> None:
        log.info(f"Identifying to {self.master_uri}...")
        await self.websocket.send(f"Identify {self.nid}:{self.link_type}:{self.secret}")
        response: Package = await self.receive()
        if not response.source == "<server>":
            raise InvalidServerResponseError("Received a non-service package before identification.")
        if "type" not in response.data:
            raise InvalidServerResponseError("Missing 'type' in response data")
        if response.data["type"] == "error":
            raise ConnectionClosedError(f"Identification error: {response.data['type']}")
        assert response.data["type"] == "success"
        self.identify_event.set()
        log.info(f"Identified successfully!")

    @requires_identification
    async def send(self, package: Package):
        await self.websocket.send(package.to_json_bytes())
        log.debug(f"Sent package: {package}")

    @requires_identification
    async def request(self, message, destination):
        package = Package(message, source=self.nid, destination=destination)
        request = PendingRequest(loop=self._loop)
        self._pending_requests[package.source_conv_id] = request
        await self.send(package)
        log.debug(f"Sent request: {message} -> {destination}")
        await request.event.wait()
        response: dict = request.data
        log.debug(f"Received response: {request} -> {response}")
        return response

    async def run(self, loops: numbers.Real = math.inf):
        """Blockingly run the Link."""
        log.debug(f"Running main client loop for {self.nid}.")
        if self.error_event.is_set():
            raise ConnectionClosedError("RoyalnetLinks can't be rerun after an error.")
        while loops:
            loops -= 1
            if not self.connect_event.is_set():
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
            response_package: Package = package.reply(response)
            await self.send(response_package)
            log.debug(f"Replied to request {response_package.source_conv_id}: {response_package}")
