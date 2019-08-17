"""The production Royalnet, active at @royalgamesbot on Telegram and Royalbot on Discord."""

import os
import asyncio
import logging
from royalnet.bots import DiscordBot, DiscordConfig, TelegramBot, TelegramConfig
from royalnet.commands import *
# noinspection PyUnresolvedReferences
from royalnet.commands import DebugCreateCommand
from royalnet.commands import ErrorHandlerCommand
from royalnet.network import RoyalnetServer, RoyalnetConfig

loop = asyncio.get_event_loop()

log = logging.root
stream_handler = logging.StreamHandler()
stream_handler.formatter = logging.Formatter("{asctime}\t{name}\t{levelname}\t{message}", style="{")
log.addHandler(stream_handler)
log.setLevel(logging.INFO)

commands = [PingCommand, SummonCommand, PlayCommand, SkipCommand, PlaymodeCommand, PauseCommand, QueueCommand]

address, port = "127.0.0.1", 1234

print("Starting master...")
master = RoyalnetServer(address, port, os.environ["MASTER_KEY"])
loop.run_until_complete(master.start())

print("Starting bots...")
ds_bot = DiscordBot(discord_config=DiscordConfig(os.environ["DS_AK"]),
                    royalnet_config=RoyalnetConfig(f"ws://{address}:{port}", os.environ["MASTER_KEY"]),
                    database_config=None,
                    commands=commands,
                    error_command=ErrorHandlerCommand,
                    missing_command=MissingCommand)
tg_bot = TelegramBot(telegram_config=TelegramConfig(os.environ["TG_AK"]),
                     royalnet_config=RoyalnetConfig(f"ws://{address}:{port}", os.environ["MASTER_KEY"]),
                     database_config=None,
                     commands=commands,
                     error_command=ErrorHandlerCommand,
                     missing_command=MissingCommand)
loop.create_task(tg_bot.run())
loop.create_task(ds_bot.run())

print("Running loop...")
loop.run_forever()
