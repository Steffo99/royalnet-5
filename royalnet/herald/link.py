from typing import *
import asyncio as aio
import uuid
import functools
import logging
import websockets
from .package import Package
from .request import Request
from .response import Response, ResponseSuccess, ResponseFailure
from .broadcast import Broadcast
from .errors import ConnectionClosedError, InvalidServerResponseError
from .config import Config


log = logging.getLogger(__name__)


class PendingRequest:
    def __init__(self, *, loop: aio.AbstractEventLoop = None):
        if loop is None:
            self.loop = aio.get_event_loop()
        else:
            self.loop = loop
        self.event: aio.Event = aio.Event(loop=loop)
        self.data: Optional[dict] = None

    def __repr__(self):
        if self.event.is_set():
            return f"<{self.__class__.__qualname__}: {self.data.__class__.__name__}>"
        return f"<{self.__class__.__qualname__}>"

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


class Link:
    def __init__(self, config: Config, request_handler, *,
                 loop: aio.AbstractEventLoop = None):
        self.config: Config = config
        self.nid: str = str(uuid.uuid4())
        self.websocket: Optional["websockets.WebSocketClientProtocol"] = None
        self.request_handler: Callable[[Union[Request, Broadcast]],
                                       Awaitable[Response]] = request_handler
        self._pending_requests: Dict[str, PendingRequest] = {}
        if loop is None:
            self._loop = aio.get_event_loop()
        else:
            self._loop = loop
        self.error_event: aio.Event = aio.Event(loop=self._loop)
        self.connect_event: aio.Event = aio.Event(loop=self._loop)
        self.identify_event: aio.Event = aio.Event(loop=self._loop)

    def __repr__(self):
        if self.identify_event.is_set():
            return f"<{self.__class__.__qualname__} (identified)>"
        elif self.connect_event.is_set():
            return f"<{self.__class__.__qualname__} (connected)>"
        elif self.error_event.is_set():
            return f"<{self.__class__.__qualname__} (error)>"
        else:
            return f"<{self.__class__.__qualname__} (disconnected)>"

    async def connect(self):
        """Connect to the :class:`Server` at :attr:`.config.url`."""
        log.debug(f"Connecting to Herald Server at {self.config.url}...")
        self.websocket = await websockets.connect(self.config.url, loop=self._loop)
        self.connect_event.set()
        log.debug(f"Connected!")

    @requires_connection
    async def receive(self) -> Package:
        """Recieve a :py:class:`Package` from the :py:class:`Server`.

        Raises:
            :exc:`ConnectionClosedError` if the connection is closed."""
        try:
            jbytes: bytes = await self.websocket.recv()
            package: Package = Package.from_json_bytes(jbytes)
        except websockets.ConnectionClosed:
            self.error_event.set()
            self.connect_event.clear()
            self.identify_event.clear()
            log.warning(f"Herald Server connection closed: {self.config.url}")
            # What to do now? Let's just reraise.
            raise ConnectionClosedError()
        if self.identify_event.is_set() and package.destination != self.nid:
            raise InvalidServerResponseError("Package is not addressed to this NetworkLink.")
        log.debug(f"Received package: {package}")
        return package

    @requires_connection
    async def identify(self) -> None:
        log.debug(f"Identifying...")
        await self.websocket.send(f"Identify {self.nid}:{self.config.name}:{self.config.secret}")
        response: Package = await self.receive()
        if not response.source == "<server>":
            raise InvalidServerResponseError("Received a non-service package before identification.")
        if "type" not in response.data:
            raise InvalidServerResponseError("Missing 'type' in response data")
        if response.data["type"] == "error":
            raise ConnectionClosedError(f"Identification error: {response.data['type']}")
        assert response.data["type"] == "success"
        self.identify_event.set()
        log.debug(f"Identified successfully!")

    @requires_identification
    async def send(self, package: Package):
        """Send a package to the :class:`Server`."""
        log.debug(f"Trying to send package: {package}")
        try:
            jbytes = package.to_json_bytes()
        except TypeError as e:
            log.fatal(f"Could not send package: {' '.join(e.args)}")
            raise
        await self.websocket.send(jbytes)
        log.debug(f"Sent package: {package}")

    @requires_identification
    async def broadcast(self, destination: str, broadcast: Broadcast) -> None:
        package = Package(broadcast.to_dict(), source=self.nid, destination=destination)
        await self.send(package)
        log.debug(f"Sent broadcast to {destination}: {broadcast}")

    @requires_identification
    async def request(self, destination: str, request: Request) -> Response:
        if destination.startswith("*"):
            raise ValueError("requests cannot have multiple destinations")
        package = Package(request.to_dict(), source=self.nid, destination=destination)
        request = PendingRequest(loop=self._loop)
        self._pending_requests[package.source_conv_id] = request
        await self.send(package)
        log.debug(f"Sent request to {destination}: {request}")
        await request.event.wait()
        if request.data["type"] == "ResponseSuccess":
            response: Response = ResponseSuccess.from_dict(request.data)
        elif request.data["type"] == "ResponseFailure":
            response: Response = ResponseFailure.from_dict(request.data)
        else:
            raise TypeError("Unknown response type")
        log.debug(f"Received from {destination}: {request} -> {response}")
        return response

    async def run(self):
        """Blockingly run the Link."""
        log.debug(f"Running link: {self.config.name}")
        if self.error_event.is_set():
            raise ConnectionClosedError("RoyalnetLinks can't be rerun after an error.")
        while True:
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
            elif package.data["msg_type"] == "Request":
                log.debug(f"Received request {package.source_conv_id}: {package}")
                response: Response = await self.request_handler(Request.from_dict(package.data))
                response_package: Package = package.reply(response.to_dict())
                await self.send(response_package)
                log.debug(f"Replied to request {response_package.source_conv_id}: {response_package}")
            # Package is a broadcast
            elif package.data["msg_type"] == "Broadcast":
                log.debug(f"Received broadcast {package.source_conv_id}: {package}")
                await self.request_handler(Broadcast.from_dict(package.data))
