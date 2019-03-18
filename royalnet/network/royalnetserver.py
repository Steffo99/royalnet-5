import typing
import websockets
import re
import datetime
from .messages import Message, ErrorMessage, BadMessage, InvalidSecretErrorMessage, IdentifySuccessfulMessage
from .packages import Package, TwoWayPackage


class ConnectedClient:
    def __init__(self, socket: websockets.WebSocketServerProtocol):
        self.socket: websockets.WebSocketServerProtocol = socket
        self.nid: str = None
        self.link_type: str = None
        self.connection_datetime: datetime.datetime = datetime.datetime.now()

    @property
    def is_identified(self) -> bool:
        return bool(self.nid)


class RoyalnetServer:
    def __init__(self, required_secret: str):
        self.required_secret: str = required_secret
        self.connected_clients: typing.List[ConnectedClient] = {}
        self.server: websockets.server.WebSocketServer = websockets.server

    def find_client_by_nid(self, nid: str):
        return [client for client in self.connected_clients if client.nid == nid][0]

    async def listener(self, websocket: websockets.server.WebSocketServerProtocol, request_uri: str):
        connected_client = ConnectedClient(websocket)
        # Wait for identification
        identify_msg = websocket.recv()
        if not isinstance(identify_msg, str):
            websocket.send(BadMessage("Invalid identification message (not a str)"))
            return
        identification = re.match(r"Identify ([A-Za-z0-9\-]+):([a-z]+):([A-Za-z0-9\-])", identify_msg)
        if identification is None:
            websocket.send(BadMessage("Invalid identification message (regex failed)"))
            return
        secret = identification.group(3)
        if secret != self.required_secret:
            websocket.send(InvalidSecretErrorMessage("Invalid secret"))
            return
        # Identification successful
        connected_client.nid = identification.group(1)
        connected_client.link_type = identification.group(2)
        self.connected_clients.append(connected_client)
        # Main loop
        while True:
            pass



