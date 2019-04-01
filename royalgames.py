import os
import asyncio
from royalnet.bots import TelegramBot
from royalnet.commands import PingCommand, ShipCommand, SmecdsCommand, ColorCommand, CiaoruoziCommand, SyncCommand
from royalnet.commands.debug_create import DebugCreateCommand
from royalnet.network import RoyalnetServer

loop = asyncio.get_event_loop()

commands = [PingCommand, ShipCommand, SmecdsCommand, ColorCommand, CiaoruoziCommand, DebugCreateCommand, SyncCommand]

master = RoyalnetServer("localhost", 1234, "sas")
tg_bot = TelegramBot(os.environ["TG_AK"], "localhost:1234", "sas", commands, "sqlite://")
loop.create_task(master.run())
loop.create_task(tg_bot.run())
print("Starting loop...")
loop.run_forever()
