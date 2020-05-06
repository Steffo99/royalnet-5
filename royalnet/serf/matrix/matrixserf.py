from typing import *
import logging
import datetime
import asyncio as aio
import royalnet.backpack as rb
import royalnet.commands as rc
import royalnet.utils as ru
from ..serf import Serf
from .escape import escape
import nio

log = logging.getLogger(__name__)


class MatrixSerf(Serf):
    """A serf that connects to `Matrix <https://matrix.org/>`_ as an user."""
    interface_name = "matrix"

    _identity_table = rb.tables.Matrix
    _identity_column = "matrix_id"

    def __init__(self,
                 loop: aio.AbstractEventLoop,
                 alchemy_cfg: Dict[str, Any],
                 herald_cfg: Dict[str, Any],
                 sentry_cfg: Dict[str, Any],
                 packs_cfg: Dict[str, Any],
                 serf_cfg: Dict[str, Any],
                 **_):
        if nio is None:
            raise ImportError("'matrix' extra is not installed")

        super().__init__(loop=loop,
                         alchemy_cfg=alchemy_cfg,
                         herald_cfg=herald_cfg,
                         sentry_cfg=sentry_cfg,
                         packs_cfg=packs_cfg,
                         serf_cfg=serf_cfg)

        self.client: Optional[nio.AsyncClient] = None

        self.homeserver: str = serf_cfg["homeserver"]
        self.matrix_id: str = serf_cfg["matrix_id"]
        self.password: str = serf_cfg["password"]

        self._started_timestamp: Optional[int] = None

        self.Data: Type[rc.CommandData] = self.data_factory()

    def interface_factory(self) -> Type[rc.CommandInterface]:
        # noinspection PyPep8Naming
        GenericInterface = super().interface_factory()

        # noinspection PyMethodParameters,PyAbstractClass
        class DiscordInterface(GenericInterface):
            name = self.interface_name
            prefix = "!"

        return DiscordInterface

    def data_factory(self) -> Type[rc.CommandData]:
        # noinspection PyMethodParameters,PyAbstractClass
        class MatrixData(rc.CommandData):
            def __init__(data,
                         interface: rc.CommandInterface,
                         loop: aio.AbstractEventLoop,
                         room: nio.MatrixRoom,
                         event: nio.Event):
                super().__init__(interface=interface, loop=loop)
                data.room: nio.MatrixRoom = room
                data.event: nio.Event = event

            async def reply(data, text: str):
                await self.client.room_send(room_id=data.room.room_id, message_type="m.room.message", content={
                    "msgtype": "m.text",
                    "body": escape(text)
                })

            async def get_author(data, error_if_none=False):
                user: str = data.event.sender
                query = data.session.query(self.master_table)
                for link in self.identity_chain:
                    query = query.join(link.mapper.class_)
                query = query.filter(self.identity_column == user)
                result = await ru.asyncify(query.one_or_none)
                if result is None and error_if_none:
                    raise rc.CommandError("You must be registered to use this command.")
                return result

            # Delete invoking does not really make sense on Matrix

        return MatrixData

    async def handle_message(self, room: "nio.MatrixRoom", event: "nio.RoomMessageText"):
        # Skip events happened before the startup of the Serf
        if event.server_timestamp < self._started_timestamp:
            return
        # Find the text in the event
        text = event.body
        # Skip non-command events
        if not text.startswith("!"):
            return
        # Find and clean parameters
        command_text, *parameters = text.split(" ")
        # Don't use a case-sensitive command name
        command_name = command_text.lower()
        # Find the command
        try:
            command = self.commands[command_name]
        except KeyError:
            # Skip the message
            return
        # Send typing
        await self.client.room_typing(room_id=room.room_id, typing_state=True)
        # Open an alchemy session, if available
        if self.alchemy is not None:
            session = await ru.asyncify(self.alchemy.Session)
        else:
            session = None
        # Prepare data
        data = self.Data(interface=command.interface, loop=self.loop, room=room, event=event)
        # Call the command
        await self.call(command, data, parameters)
        # Close the alchemy session
        if session is not None:
            await ru.asyncify(session.close)

    async def run(self):
        self.client = nio.AsyncClient(self.homeserver, self.matrix_id)
        await self.client.login(self.password)
        self._started_timestamp = int(datetime.datetime.now().timestamp() * 1000)
        # matrix-nio type annotations are wrong for asyncclients
        # noinspection PyTypeChecker
        self.client.add_event_callback(self.handle_message, (nio.RoomMessageText,))
        await self.client.sync_forever()
