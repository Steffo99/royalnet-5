import os
import asyncio
import logging
from royalnet.bots import TelegramBot, DiscordBot
from royalnet.commands import *
from royalnet.commands.debug_create import DebugCreateCommand
from royalnet.commands.error_handler import ErrorHandlerCommand
from royalnet.network import RoyalnetServer
from royalnet.database.tables import Royal, Telegram, Discord

loop = asyncio.get_event_loop()

log = logging.root
log.addHandler(logging.StreamHandler())
logging.getLogger("royalnet.bots.telegram").setLevel(logging.DEBUG)
logging.getLogger("royalnet.bots.discord").setLevel(logging.DEBUG)
logging.getLogger("royalnet.network.royalnetserver").setLevel(logging.DEBUG)

commands = [PingCommand, ShipCommand, SmecdsCommand, ColorCommand, CiaoruoziCommand, DebugCreateCommand, SyncCommand,
            AuthorCommand, DiarioCommand, RageCommand, DateparserCommand, ReminderCommand, KvactiveCommand, KvCommand,
            KvrollCommand, VideoinfoCommand, SummonCommand, PlayCommand]

master = RoyalnetServer("localhost", 1234, "sas")
tg_bot = TelegramBot(os.environ["TG_AK"], "ws://localhost:1234", "sas", commands, os.environ["DB_PATH"], Royal, Telegram, "tg_id", error_command=ErrorHandlerCommand)
ds_bot = DiscordBot(os.environ["DS_AK"], "ws://localhost:1234", "sas", commands, os.environ["DB_PATH"], Royal, Discord, "discord_id", error_command=ErrorHandlerCommand)
loop.run_until_complete(master.run())
# Dirty hack, remove me asap
loop.create_task(tg_bot.run())
loop.create_task(ds_bot.run())
print("Commands enabled:")
print(tg_bot.generate_botfather_command_string())
print("Starting loop...")
loop.run_forever()
