import os
import asyncio
from royalnet.bots import TelegramBot
from royalnet.commands import PingCommand, ShipCommand, SmecdsCommand, ColorCommand, CiaoruoziCommand, SyncCommand
from royalnet.commands.debug_create import DebugCreateCommand
from royalnet.commands.debug_author import DebugAuthorCommand
from royalnet.network import RoyalnetServer
from royalnet.database.tables import Royal, Telegram

loop = asyncio.get_event_loop()

commands = [PingCommand, ShipCommand, SmecdsCommand, ColorCommand, CiaoruoziCommand, DebugCreateCommand, SyncCommand,
            DebugAuthorCommand]

master = RoyalnetServer("localhost", 1234, "sas")
tg_bot = TelegramBot(os.environ["TG_AK"], "localhost:1234", "sas", commands, os.environ["DB_PATH"], Royal, Telegram, "tg_id")
loop.create_task(master.run())
loop.create_task(tg_bot.run())
print("Starting loop...")
loop.run_forever()
