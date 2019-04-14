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

tg_log = logging.getLogger("royalnet.bots.telegram")
tg_log.addHandler(logging.StreamHandler())
tg_log.setLevel(logging.DEBUG)
ds_log = logging.getLogger("royalnet.bots.discord")
ds_log.addHandler(logging.StreamHandler())
ds_log.setLevel(logging.DEBUG)
rygnet_log = logging.getLogger("royalnet.network.server")
rygnet_log.addHandler(logging.StreamHandler())
rygnet_log.setLevel(logging.DEBUG)

commands = [PingCommand, ShipCommand, SmecdsCommand, ColorCommand, CiaoruoziCommand, DebugCreateCommand, SyncCommand,
            AuthorCommand, DiarioCommand, RageCommand, DateparserCommand, ReminderCommand, KvactiveCommand, KvCommand,
            KvrollCommand, VideoinfoCommand, SummonCommand]

master = RoyalnetServer("localhost", 1234, "sas")
tg_bot = TelegramBot(os.environ["TG_AK"], "ws://localhost:1234", "sas", commands, os.environ["DB_PATH"], Royal, Telegram, "tg_id", error_command=ErrorHandlerCommand)
ds_bot = DiscordBot(os.environ["DS_AK"], "ws://localhost:1234", "sas", commands, os.environ["DB_PATH"], Royal, Discord, "discord_id", error_command=ErrorHandlerCommand)
loop.create_task(master.run())
loop.create_task(tg_bot.run())
loop.create_task(ds_bot.run())
print("Commands enabled:")
print(tg_bot.generate_botfather_command_string())
print("Starting loop...")
loop.run_forever()
