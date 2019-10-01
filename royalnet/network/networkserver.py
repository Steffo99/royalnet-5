import typing
import websockets
import re
import datetime
import uuid
import asyncio
import logging as _logging
from .package import Package


log = _logging.getLogger(__name__)


class ConnectedClient:
    """The :py:class:`royalnet.network.NetworkServer`-side representation of a connected :py:class:`royalnet.network.NetworkLink`."""
    def __init__(self, socket: websockets.WebSocketServerProtocol):
        self.socket: websockets.WebSocketServerProtocol = socket
        self.nid: typing.Optional[str] = None
        self.link_type: typing.Optional[str] = None
        self.connection_datetime: datetime.datetime = datetime.datetime.now()

    @property
    def is_identified(self) -> bool:
        """Has the client sent a valid identification package?"""
        return bool(self.nid)

    async def send_service(self, msg_type: str, message: str):
        await self.send(Package({"type": msg_type, "service": message},
                                source="<server>",
                                destination=self.nid))

    async def send(self, package: Package):
        """Send a :py:class:`royalnet.network.Package` to the :py:class:`royalnet.network.NetworkLink`."""
        await self.socket.send(package.to_json_bytes())


class NetworkServer:
    def __init__(self, address: str, port: int, required_secret: str, *, loop: asyncio.AbstractEventLoop = None):
        self.address: str = address
        self.port: int = port
        self.required_secret: str = required_secret
        self.identified_clients: typing.List[ConnectedClient] = []
        self.loop = loop

    def find_client(self, *, nid: str = None, link_type: str = None) -> typing.List[ConnectedClient]:
        assert not (nid and link_type)
        if nid:
            matching = [client for client in self.identified_clients if client.nid == nid]
            assert len(matching) <= 1
            return matching
        if link_type:
            matching = [client for client in self.identified_clients if client.link_type == link_type]
            return matching or []

    async def listener(self, websocket: websockets.server.WebSocketServerProtocol, path):
        log.info(f"{websocket.remote_address} connected to the server.")
        connected_client = ConnectedClient(websocket)
        # Wait for identification
        identify_msg = await websocket.recv()
        log.debug(f"{websocket.remote_address} identified itself with: {identify_msg}.")
        if not isinstance(identify_msg, str):
            await connected_client.send_service("error", "Invalid identification message (not a str)")
            return
        identification = re.match(r"Identify ([^:\s]+):([^:\s]+):([^:\s]+)", identify_msg)
        if identification is None:
            await connected_client.send_service("error", "Invalid identification message (regex failed)")
            return
        secret = identification.group(3)
        if secret != self.required_secret:
            await connected_client.send_service("error", "Invalid secret")
            return
        # Identification successful
        connected_client.nid = identification.group(1)
        connected_client.link_type = identification.group(2)
        self.identified_clients.append(connected_client)
        log.debug(f"{websocket.remote_address} identified successfully as {connected_client.nid} ({connected_client.link_type}).")
        await connected_client.send_service("success", "Identification successful!")
        log.debug(f"{connected_client.nid}'s identification confirmed.")
        # Main loop
        while True:
            # Receive packages
            raw_bytes = await websocket.recv()
            package: Package = Package.from_json_bytes(raw_bytes)
            log.debug(f"Received package: {package}")
            # Check if the package destination is the server itself.
            if package.destination == "<server>":
                # TODO: do stuff
                pass
            # Otherwise, route the package to its destination
            # noinspection PyAsyncCall
            self.loop.create_task(self.route_package(package))

    def find_destination(self, package: Package) -> typing.List[ConnectedClient]:
        """Find a list of destinations for the package.

        Parameters:
            package: The package to find the destination of.

        Returns:
            A :py:class:`list` of :py:class:`ConnectedClients` to send the package to."""
        # Parse destination
        # Is it nothing?
        if package.destination == "<none>":
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
            # This may have some consequences
            specific_package = Package(package.data,
                                       source=package.source,
                                       destination=destination.nid,
                                       source_conv_id=package.source_conv_id,
                                       destination_conv_id=package.destination_conv_id)
            await destination.send(specific_package)

    def serve(self):
        log.debug(f"Serving on ws://{self.address}:{self.port}")
        server = self.loop.run_until_complete(websockets.serve(self.listener,
                                                               host=self.address,
                                                               port=self.port,
                                                               loop=self.loop))
        self.loop.run_forever()

    def run_blocking(self, verbose=False):
        if verbose:
            core_logger = _logging.getLogger("royalnet")
            core_logger.setLevel(_logging.DEBUG)
            stream_handler = _logging.StreamHandler()
            stream_handler.formatter = _logging.Formatter("{asctime}\t{name}\t{levelname}\t{message}", style="{")
            core_logger.addHandler(stream_handler)
            core_logger.debug("Logging setup complete.")
        if self.loop is None:
            self.loop = asyncio.get_event_loop()
        self.serve()
