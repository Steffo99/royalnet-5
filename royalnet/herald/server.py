from typing import *
import asyncio as aio
import re
import datetime
import uuid
import logging
import websockets
import royalnet.utils as ru
from .package import Package
from .config import Config


log = logging.getLogger(__name__)


class ConnectedClient:
    """The :py:class:`Server`-side representation of a connected :py:class:`Link`."""
    def __init__(self, socket: "websockets.WebSocketServerProtocol"):
        self.socket: "websockets.WebSocketServerProtocol" = socket
        self.nid: Optional[str] = None
        self.link_type: Optional[str] = None
        self.connection_datetime: datetime.datetime = datetime.datetime.now()

    def __repr__(self):
        return f"<{self.__class__.__qualname__} {self.nid}>"

    @property
    def is_identified(self) -> bool:
        """Has the client sent a valid identification package?"""
        return bool(self.nid)

    async def send_service(self, msg_type: str, message: str):
        await self.send(Package({"type": msg_type, "service": message},
                                source="<server>",
                                destination=self.nid))

    async def send(self, package: Package):
        """Send a :py:class:`Package` to the :py:class:`Link`."""
        await self.socket.send(package.to_json_bytes())


class Server:
    def __init__(self, config: Config, *, loop: aio.AbstractEventLoop = None):
        self.config: Config = config
        self.identified_clients: List[ConnectedClient] = []
        self.loop = loop

    def __repr__(self):
        return f"<{self.__class__.__qualname__}>"

    def find_client(self, *, nid: str = None, link_type: str = None) -> List[ConnectedClient]:
        assert not (nid and link_type)
        if nid:
            matching = [client for client in self.identified_clients if client.nid == nid]
            assert len(matching) <= 1
            return matching
        if link_type:
            matching = [client for client in self.identified_clients if client.link_type == link_type]
            return matching or []

    async def listener(self, websocket: "websockets.server.WebSocketServerProtocol", path):
        connected_client = ConnectedClient(websocket)
        # Wait for identification
        identify_msg = await websocket.recv()
        log.debug(f"{websocket.remote_address} identified itself with: {identify_msg}.")
        if not isinstance(identify_msg, str):
            log.warning(f"Failed Herald identification: {websocket.remote_address[0]}:{websocket.remote_address[1]}")
            await connected_client.send_service("error", "Invalid identification message (not a str)")
            return
        identification = re.match(r"Identify ([^:\s]+):([^:\s]+):([^:\s]+)", identify_msg)
        if identification is None:
            log.warning(f"Failed Herald identification: {websocket.remote_address[0]}:{websocket.remote_address[1]}")
            await connected_client.send_service("error", "Invalid identification message (regex failed)")
            return
        secret = identification.group(3)
        if secret != self.config.secret:
            log.warning(f"Invalid Herald secret: {websocket.remote_address[0]}:{websocket.remote_address[1]}")
            await connected_client.send_service("error", "Invalid secret")
            return
        # Identification successful
        connected_client.nid = identification.group(1)
        connected_client.link_type = identification.group(2)
        log.info(f"Joined the Herald: {websocket.remote_address[0]}:{websocket.remote_address[1]}"
                 f" ({connected_client.link_type})")
        self.identified_clients.append(connected_client)
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
                # Do... nothing for now?
                pass
            # Otherwise, route the package to its destination
            # noinspection PyAsyncCall
            self.loop.create_task(self.route_package(package))

    def find_destination(self, package: Package) -> List[ConnectedClient]:
        """Find a list of destinations for the package.

        Parameters:
            package: The package to find the destination of.

        Returns:
            A :class:`list` of :class:`ConnectedClient` to send the package to."""
        # Parse destination
        # Is it nothing?
        if package.destination == "<none>":
            return []
        # Is it all possible destinations?
        if package.destination == "*":
            return self.identified_clients
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
        """Executed every time a :class:`Package` is received and must be routed somewhere."""
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
        if self.config.secure:
            raise Exception("Secure servers aren't supported yet")
        log.debug(f"Serving on {self.config.url}")
        try:
            self.loop.run_until_complete(self.run())
        except OSError as e:
            log.fatal(f"OSError: {e}")
        self.loop.run_forever()

    async def run(self):
        await websockets.serve(self.listener,
                               host=self.config.address,
                               port=self.config.port,
                               loop=self.loop)

    def run_blocking(self, logging_cfg: Dict[str, Any]):
        ru.init_logging(logging_cfg)
        if self.loop is None:
            self.loop = aio.get_event_loop()
        self.serve()
