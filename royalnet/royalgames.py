"""The production Royalnet, active at @royalgamesbot on Telegram and Royalbot on Discord."""

import os
import asyncio
import logging
import sentry_sdk
from royalnet.bots import DiscordBot, DiscordConfig, TelegramBot, TelegramConfig
from royalnet.commands.royalgames import *
from royalnet.commands.debug import *
from royalnet.network import RoyalnetServer, RoyalnetConfig
from royalnet.database import DatabaseConfig
from royalnet.database.tables import Royal, Telegram, Discord

loop = asyncio.get_event_loop()

log = logging.getLogger("royalnet.bots")
stream_handler = logging.StreamHandler()
stream_handler.formatter = logging.Formatter("{asctime}\t{name}\t{levelname}\t{message}", style="{")
log.addHandler(stream_handler)


sentry_dsn = os.environ.get("SENTRY_DSN")

# noinspection PyUnreachableCode
if __debug__:
    commands = [
        CiaoruoziCommand,
        ColorCommand,
        CvCommand,
        DiarioCommand,
        Mp3Command,
        PauseCommand,
        PingCommand,
        PlayCommand,
        PlaymodeCommand,
        QueueCommand,
        RageCommand,
        ReminderCommand,
        ShipCommand,
        SkipCommand,
        SmecdsCommand,
        SummonCommand,
        VideochannelCommand,
        TriviaCommand,
        MmCommand,
        ZawarudoCommand
    ]
    log.setLevel(logging.DEBUG)
else:
    commands = [
        CiaoruoziCommand,
        ColorCommand,
        CvCommand,
        DiarioCommand,
        Mp3Command,
        PauseCommand,
        PingCommand,
        PlayCommand,
        PlaymodeCommand,
        QueueCommand,
        RageCommand,
        ReminderCommand,
        ShipCommand,
        SkipCommand,
        SmecdsCommand,
        SummonCommand,
        VideochannelCommand,
        DnditemCommand,
        DndspellCommand,
        TriviaCommand,
        MmCommand,
        ZawarudoCommand
    ]
    log.setLevel(logging.INFO)

address, port = "127.0.0.1", 1234

print("Starting master...")
master = RoyalnetServer(address, port, os.environ["MASTER_KEY"])
loop.run_until_complete(master.start())

print("Starting bots...")
ds_bot = DiscordBot(discord_config=DiscordConfig(os.environ["DS_AK"]),
                    royalnet_config=RoyalnetConfig(f"ws://{address}:{port}", os.environ["MASTER_KEY"]),
                    database_config=DatabaseConfig(os.environ["DB_PATH"], Royal, Discord, "discord_id"),
                    sentry_dsn=sentry_dsn,
                    commands=commands)
tg_bot = TelegramBot(telegram_config=TelegramConfig(os.environ["TG_AK"]),
                     royalnet_config=RoyalnetConfig(f"ws://{address}:{port}", os.environ["MASTER_KEY"]),
                     database_config=DatabaseConfig(os.environ["DB_PATH"], Royal, Telegram, "tg_id"),
                     sentry_dsn=sentry_dsn,
                     commands=commands)
loop.create_task(tg_bot.run())
loop.create_task(ds_bot.run())

print("Enabled commands:")
for command in commands:
    print(f"{command.name} - {command.description}")

print("Running loop...")
loop.run_forever()
