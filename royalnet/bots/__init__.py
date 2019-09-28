"""Various bot interfaces, and a generic class to create new ones."""

from .generic import GenericBot
from .telegram import TelegramBot
from .discord import DiscordBot

__all__ = ["TelegramBot", "DiscordBot", "GenericBot"]
