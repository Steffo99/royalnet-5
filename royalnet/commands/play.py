import typing
from ..utils import Command, Call
from ..network import Message


class PlayMessage(Message):
    def __init__(self, url: str):
        self.url: str = url


class PlaySuccessful(Message):
    pass


class PlayError(Message):
    def __init__(self, reason: str):
        self.reason: str = reason


class PlayCommand(Command):
    command_name = "play"
    command_description = "Riproduce una canzone in chat vocale."
    command_syntax = "(url)"

    @classmethod
    async def common(cls, call: Call):
        url: str = call.args[0]
        response: typing.Union[PlaySuccessful, PlayError] = await call.net_request(PlayMessage(url), "discord")
        if isinstance(response, PlayError):
            await call.reply(f"⚠️ Si è verificato un'errore nella richiesta di riproduzione:\n[c]{response.reason}[/c]")
            return
        elif isinstance(response, PlaySuccessful):
            await call.reply(f"✅ Richiesta la riproduzione di [c]{url}[/c].")
            return
        raise TypeError(f"Received unexpected response in the PlayCommand: {response.__class__.__name__}")
