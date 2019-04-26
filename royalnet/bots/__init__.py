"""Various bot interfaces, and a generic class to create new ones."""

from .generic import GenericBot
from .telegram import TelegramBot, TelegramConfig
from .discord import DiscordBot, DiscordConfig

__all__ = ["TelegramBot", "TelegramConfig", "DiscordBot", "DiscordConfig", "GenericBot"]
