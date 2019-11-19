from typing import Dict, Any
from .discordbard import DiscordBard

try:
    import discord
except ImportError:
    discord = None


class BardsDict:
    def __init__(self, client: "discord.Client"):
        if discord is None:
            raise ImportError("'discord' extra is not installed.")
        self.client: "discord.Client" = client
        self._dict: Dict["discord.Guild", DiscordBard] = dict()

    def __getitem__(self, item: "discord.Guild") -> DiscordBard:
        bard = self._dict[item]
        if bard.voice_client not in self.client.voice_clients:
            del self._dict[item]
            raise KeyError("Requested bard is disconnected and was removed from the dict.")
        return bard

    def __setitem__(self, key: "discord.Guild", value):
        if not isinstance(value, DiscordBard):
            raise TypeError(f"Cannot __setitem__ with {value.__class__.__name__}.")
        self._dict[key] = value

    def get(self, item: "discord.Guild", default: Any = None) -> Any:
        try:
            return self[item]
        except KeyError:
            return default
