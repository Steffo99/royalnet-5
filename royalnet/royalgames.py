import os
import asyncio
import logging
from royalnet.bots import DiscordBot, DiscordConfig, TelegramBot, TelegramConfig
from royalnet.commands import *
# noinspection PyUnresolvedReferences
from royalnet.commands.debug_create import DebugCreateCommand
from royalnet.commands.error_handler import ErrorHandlerCommand
from royalnet.network import RoyalnetServer, RoyalnetConfig
from royalnet.database import DatabaseConfig
from royalnet.database.tables import Royal, Telegram, Discord

loop = asyncio.get_event_loop()

log = logging.root
stream_handler = logging.StreamHandler()
stream_handler.formatter = logging.Formatter("{asctime}\t{name}\t{levelname}\t{message}", style="{")
log.addHandler(stream_handler)
log.setLevel(logging.INFO)

commands = [PingCommand, ShipCommand, SmecdsCommand, ColorCommand, CiaoruoziCommand, SyncCommand,
            DiarioCommand, RageCommand, ReminderCommand, KvactiveCommand, KvCommand,
            KvrollCommand, SummonCommand, PlayCommand, SkipCommand, PlaymodeCommand,
            VideochannelCommand, CvCommand, PauseCommand, QueueCommand, RoyalnetprofileCommand]

# noinspection PyUnreachableCode
if __debug__:
    commands = [DebugCreateCommand, VideoinfoCommand, DateparserCommand, AuthorCommand, *commands]

address, port = "127.0.0.1", 1234

print("Starting master...")
master = RoyalnetServer(address, port, os.environ["MASTER_KEY"])
loop.run_until_complete(master.start())

print("Starting bots...")
ds_bot = DiscordBot(discord_config=DiscordConfig(os.environ["DS_AK"]),
                    royalnet_config=RoyalnetConfig(f"ws://{address}:{port}", os.environ["MASTER_KEY"]),
                    database_config=DatabaseConfig(os.environ["DB_PATH"], Royal, Discord, "discord_id"),
                    commands=commands,
                    error_command=ErrorHandlerCommand,
                    missing_command=MissingCommand)
tg_bot = TelegramBot(telegram_config=TelegramConfig(os.environ["TG_AK"]),
                     royalnet_config=RoyalnetConfig(f"ws://{address}:{port}", os.environ["MASTER_KEY"]),
                     database_config=DatabaseConfig(os.environ["DB_PATH"], Royal, Telegram, "tg_id"),
                     commands=commands,
                     error_command=ErrorHandlerCommand,
                     missing_command=MissingCommand)
loop.create_task(tg_bot.run())
loop.create_task(ds_bot.run())

print("Running loop...")
loop.run_forever()
