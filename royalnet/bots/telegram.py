import telegram
import asyncio
import typing
from ..commands import PingCommand
from ..utils import asyncify, Call


class TelegramBot:
    def __init__(self, api_key: str):
        self.bot = telegram.Bot(api_key)
        self.should_run = False
        self.offset = -100
        self.commands = {
            "/ping": PingCommand
        }

        class TelegramCall(Call):
            interface_name = "telegram"
            interface_obj = self

            async def reply(call, text: str):
                await asyncify(call.channel.send_message, text, parse_mode="HTML")
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
            return
        # Call the command
        return await self.Call(message.chat, command).run()
