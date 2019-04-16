import typing
from ..utils import Command, Call
from ..network import Message, RequestSuccessful, RequestError
from ..bots.discord import PlayMessage


class PlayCommand(Command):
    command_name = "play"
    command_description = "Riproduce una canzone in chat vocale."
    command_syntax = "(url)"

    @classmethod
    async def common(cls, call: Call):
        url: str = call.args[0]
        response: typing.Union[RequestSuccessful, RequestError] = await call.net_request(PlayMessage(url), "discord")
        response.raise_on_error()
        await call.reply(f"✅ Richiesta la riproduzione di [c]{url}[/c].")
