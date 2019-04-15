import discord
from .youtubedl import YtdlFile


class DiscordYtdlFile(YtdlFile):
    def create_audio_source(self):
        return discord.FFmpegPCMAudio(self.filename)
