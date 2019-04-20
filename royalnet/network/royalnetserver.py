import typing
import websockets
import re
import datetime
import pickle
import uuid
import asyncio
import logging as _logging
from .messages import InvalidPackageEM, InvalidSecretEM, IdentifySuccessfulMessage
from .packages import Package

default_loop = asyncio.get_event_loop()
log = _logging.getLogger(__name__)


class ConnectedClient:
    def __init__(self, socket: websockets.WebSocketServerProtocol):
        self.socket: websockets.WebSocketServerProtocol = socket
        self.nid: typing.Optional[str] = None
        self.link_type: typing.Optional[str] = None
        self.connection_datetime: datetime.datetime = datetime.datetime.now()

    @property
    def is_identified(self) -> bool:
        return bool(self.nid)

    async def send(self, package: Package):
        await self.socket.send(package.pickle())


class RoyalnetServer:
    def __init__(self, address: str, port: int, required_secret: str, *, loop: asyncio.AbstractEventLoop = default_loop):
        self.address: str = address
        self.port: int = port
        self.required_secret: str = required_secret
        self.identified_clients: typing.List[ConnectedClient] = []
        self._loop: asyncio.AbstractEventLoop = loop

    def find_client(self, *, nid: str = None, link_type: str = None) -> typing.List[ConnectedClient]:
        assert not (nid and link_type)
        if nid:
            matching = [client for client in self.identified_clients if client.nid == nid]
            assert len(matching) <= 1
            return matching
        if link_type:
            matching = [client for client in self.identified_clients if client.link_type == link_type]
            return matching or []

    async def listener(self, websocket: websockets.server.WebSocketServerProtocol, request_uri: str):
        log.info(f"{websocket.remote_address} connected to the server.")
        connected_client = ConnectedClient(websocket)
        # Wait for identification
        identify_msg = await websocket.recv()
        log.debug(f"{websocket.remote_address} identified itself with: {identify_msg}.")
        if not isinstance(identify_msg, str):
            await websocket.send(InvalidPackageEM("Invalid identification message (not a str)"))
            return
        identification = re.match(r"Identify ([^:\s]+):([^:\s]+):([^:\s]+)", identify_msg)
        if identification is None:
            await websocket.send(InvalidPackageEM("Invalid identification message (regex failed)"))
            return
        secret = identification.group(3)
        if secret != self.required_secret:
            await websocket.send(InvalidSecretEM("Invalid secret"))
            return
        # Identification successful
        connected_client.nid = identification.group(1)
        connected_client.link_type = identification.group(2)
        self.identified_clients.append(connected_client)
        log.debug(f"{websocket.remote_address} identified successfully as {connected_client.nid} ({connected_client.link_type}).")
        await connected_client.send(Package(IdentifySuccessfulMessage(), connected_client.nid, "__master__"))
        log.debug(f"{connected_client.nid}'s identification confirmed.")
        # Main loop
        while True:
            # Receive packages
            raw_pickle = await websocket.recv()
            package: Package = pickle.loads(raw_pickle)
            log.debug(f"Received package: {package}")
            # Check if the package destination is the server itself.
            if package.destination == "__master__":
                # TODO: do stuff
                pass
            # Otherwise, route the package to its destination
            # noinspection PyAsyncCall
            self._loop.create_task(self.route_package(package))

    def find_destination(self, package: Package) -> typing.List[ConnectedClient]:
        """Find a list of destinations for the sent packages"""
        # Parse destination
        # Is it nothing?
        if package.destination == "NULL":
            return []
        # Is it a valid nid?
        try:
            destination = str(uuid.UUID(package.destination))
        except ValueError:
            pass
        else:
            return self.find_client(nid=destination)
        # Is it a link_type?
        return self.find_client(link_type=package.destination)

    async def route_package(self, package: Package) -> None:
        """Executed every time a package is received and must be routed somewhere."""
        destinations = self.find_destination(package)
        log.debug(f"Routing package: {package} -> {destinations}")
        for destination in destinations:
            specific_package = Package(package.data, destination.nid, package.source,
                                       source_conv_id=package.source_conv_id,
                                       destination_conv_id=package.destination_conv_id)
            await destination.send(specific_package)

    async def serve(self):
        await websockets.serve(self.listener, host=self.address, port=self.port)

    async def start(self):
        log.debug(f"Starting main server loop for __master__ on ws://{self.address}:{self.port}")
        # noinspection PyAsyncCall
        self._loop.create_task(self.serve())
