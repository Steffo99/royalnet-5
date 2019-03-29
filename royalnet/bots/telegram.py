import telegram
import asyncio
import typing
import logging as _logging
from ..commands import NullCommand
from ..utils import asyncify, Call, Command
from ..network import RoyalnetLink, Message


loop = asyncio.get_event_loop()
log = _logging.getLogger(__name__)


async def todo(message: Message):
    pass


class TelegramBot:
    def __init__(self,
                 api_key: str,
                 master_server_uri: str,
                 master_server_secret: str,
                 commands: typing.List[typing.Type[Command]],
                 missing_command: Command = NullCommand):
        self.bot: telegram.Bot = telegram.Bot(api_key)
        self.should_run: bool = False
        self.offset: int = -100
        self.missing_command = missing_command
        self.network: RoyalnetLink = RoyalnetLink(master_server_uri, master_server_secret, "telegram", todo)
        # Generate commands
        self.commands = {}
        for command in commands:
            self.commands[f"/{command.command_name}"] = command

        class TelegramCall(Call):
            interface_name = "telegram"
            interface_obj = self

            async def reply(self, text: str):
                await asyncify(self.channel.send_message, text, parse_mode="HTML")

            async def net_request(self, message: Message, destination: str):
                response = await self.network.request(message, destination)
                return response

        self.Call = TelegramCall

    async def run(self):
        self.should_run = True
        while self.should_run:
            # Get the latest 100 updates
            last_updates: typing.List[telegram.Update] = await asyncify(self.bot.get_updates, offset=self.offset)
            # Handle updates
            for update in last_updates:
                # noinspection PyAsyncCall
                asyncio.create_task(self.handle_update(update))
            # Recalculate offset
            try:
                self.offset = last_updates[-1].update_id + 1
            except IndexError:
                pass
            # Wait for a while  TODO: use long polling
            await asyncio.sleep(1)

    async def handle_update(self, update: telegram.Update):
        # Skip non-message updates
        if update.message is None:
            return
        message: telegram.Message = update.message
        # Skip no-text messages
        if message.text is None:
            return
        text: str = message.text
        # Find and clean parameters
        command_text, *parameters = text.split(" ")
        command_text.replace(f"@{self.bot.username}", "")
        # Find the function
        try:
            command = self.commands[command_text]
        except KeyError:
            # Skip inexistent commands
            command = self.missing_command
        # Call the command
        return await self.Call(message.chat, command, *parameters, update=update).run()

    async def handle_net_request(self, message: Message):
        pass