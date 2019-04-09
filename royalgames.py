import os
import asyncio
from royalnet.bots import TelegramBot
from royalnet.commands import PingCommand, ShipCommand, SmecdsCommand, ColorCommand, CiaoruoziCommand, SyncCommand, DiarioCommand, RageCommand
from royalnet.commands.debug_create import DebugCreateCommand
from royalnet.commands.author import AuthorCommand
from royalnet.commands.dateparser import DateparserCommand
from royalnet.commands.error_handler import ErrorHandlerCommand
from royalnet.network import RoyalnetServer
from royalnet.database.tables import Royal, Telegram

loop = asyncio.get_event_loop()

commands = [PingCommand, ShipCommand, SmecdsCommand, ColorCommand, CiaoruoziCommand, DebugCreateCommand, SyncCommand,
            AuthorCommand, DiarioCommand, RageCommand, DateparserCommand]

master = RoyalnetServer("localhost", 1234, "sas")
tg_bot = TelegramBot(os.environ["TG_AK"], "localhost:1234", "sas", commands, os.environ["DB_PATH"], Royal, Telegram, "tg_id", error_command=ErrorHandlerCommand)
loop.create_task(master.run())
loop.create_task(tg_bot.run())
print("Commands enabled:")
print(tg_bot.generate_botfather_command_string())
print("Starting loop...")
loop.run_forever()
